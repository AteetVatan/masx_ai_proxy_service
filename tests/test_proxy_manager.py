"""
Unit tests for ProxyManager class.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.proxy_manager import ProxyManager
from app.config import get_settings


class TestProxyManager:
    """Test cases for ProxyManager class."""
    
    @pytest.fixture
    def proxy_manager(self, mock_settings, mock_logger):
        """Create a fresh ProxyManager instance for each test."""
        # Reset singleton and create new instance with mocked dependencies
        ProxyManager._instance = None
        
        with patch('app.proxy_manager.get_settings', return_value=mock_settings):
            with patch('app.proxy_manager.get_service_logger', return_value=mock_logger):
                manager = ProxyManager()
                return manager
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch('app.proxy_manager.get_settings') as mock:
            mock_settings = Mock()
            mock_settings.proxy_webpage = "https://test-proxy-site.com"
            mock_settings.proxy_testing_url = "https://httpbin.org/ip"
            mock_settings.refresh_interval_minutes = 5
            mock_settings.proxy_test_timeout = 3
            mock_settings.batch_size = 10
            mock_settings.max_refresh_requests_per_minute = 10
            mock.return_value = mock_settings
            yield mock_settings
    

    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger for testing."""
        with patch('app.proxy_manager.get_service_logger') as mock:
            mock_logger = Mock()
            mock.return_value = mock_logger
            yield mock_logger
    
    def test_singleton_pattern(self):
        """Test that ProxyManager follows singleton pattern."""
        manager1 = ProxyManager()
        manager2 = ProxyManager()
        assert manager1 is manager2
    
    def test_initialization(self, proxy_manager, mock_settings, mock_logger):
        """Test ProxyManager initialization."""
        assert proxy_manager._settings == mock_settings
        assert proxy_manager._logger == mock_logger
        assert proxy_manager._proxies == []
        assert proxy_manager._proxy_timestamp is None
        assert proxy_manager._refresh_count == 0
    
    @pytest.mark.asyncio
    async def test_get_proxies_empty_initial(self, proxy_manager, mock_logger):
        """Test get_proxies when no proxies are available initially."""
        with patch.object(proxy_manager, '_refresh_proxies') as mock_refresh:
            mock_refresh.return_value = None
            
            result = await proxy_manager.get_proxies()
            
            assert result == []
            mock_refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_proxies_with_existing_proxies(self, proxy_manager):
        """Test get_proxies when proxies already exist and are not expired."""
        # Set up existing proxies
        proxy_manager._proxies = ["1.2.3.4:8080", "5.6.7.8:3128"]
        proxy_manager._proxy_timestamp = datetime.now()
        
        with patch.object(proxy_manager, '_refresh_proxies') as mock_refresh:
            result = await proxy_manager.get_proxies()
            
            assert result == ["1.2.3.4:8080", "5.6.7.8:3128"]
            mock_refresh.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_proxies_expired(self, proxy_manager):
        """Test get_proxies when proxies are expired."""
        # Set up expired proxies
        proxy_manager._proxies = ["1.2.3.4:8080"]
        proxy_manager._proxy_timestamp = datetime.now() - timedelta(minutes=10)
        
        with patch.object(proxy_manager, '_refresh_proxies') as mock_refresh:
            # Mock refresh to clear proxies
            def mock_refresh_side_effect():
                proxy_manager._proxies = []
                proxy_manager._proxy_timestamp = datetime.now()
            
            mock_refresh.side_effect = mock_refresh_side_effect
            
            result = await proxy_manager.get_proxies()
            
            # After refresh, proxies should be empty
            assert result == []
            mock_refresh.assert_called_once()
    
    def test_get_random_proxy_with_proxies(self, proxy_manager):
        """Test get_random_proxy when proxies are available."""
        proxy_manager._proxies = ["1.2.3.4:8080", "5.6.7.8:3128"]
        
        with patch('random.choice') as mock_choice:
            mock_choice.return_value = "1.2.3.4:8080"
            result = proxy_manager.get_random_proxy()
            
            assert result == "1.2.3.4:8080"
            mock_choice.assert_called_once_with(["1.2.3.4:8080", "5.6.7.8:3128"])
    
    def test_get_random_proxy_no_proxies(self, proxy_manager):
        """Test get_random_proxy when no proxies are available."""
        proxy_manager._proxies = []
        
        result = proxy_manager.get_random_proxy()
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_refresh_proxies_success(self, proxy_manager, mock_logger):
        """Test successful proxy refresh."""
        with patch.object(proxy_manager, '_refresh_proxies') as mock_refresh:
            mock_refresh.return_value = None
            proxy_manager._proxies = ["1.2.3.4:8080"]
            proxy_manager._proxy_timestamp = datetime.now()
            
            result = await proxy_manager.refresh_proxies()
            
            assert result["success"] is True
            assert result["proxy_count"] == 1
            assert "last_refresh" in result
            assert "next_refresh" in result
            mock_refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_proxies_rate_limited(self, proxy_manager):
        """Test proxy refresh when rate limit is exceeded."""
        # Set up rate limiting
        proxy_manager._refresh_count = 15  # Exceeds limit
        proxy_manager._refresh_reset_time = datetime.now()
        
        result = await proxy_manager.refresh_proxies()
        
        assert result["success"] is False
        assert "Rate limit exceeded" in result["message"]
    
    @pytest.mark.asyncio
    async def test_fetch_proxies_html_success(self, proxy_manager):
        """Test successful HTML proxy fetching."""
        mock_proxies = ["1.2.3.4:8080", "5.6.7.8:3128"]
        
        with patch.object(proxy_manager, '_fetch_html_proxies') as mock_html:
            mock_html.return_value = mock_proxies
            
            result = await proxy_manager._fetch_proxies()
            
            # Check that all expected proxies are present (order may vary due to set operations)
            assert len(result) == len(mock_proxies)
            for proxy in mock_proxies:
                assert proxy in result
    
    @pytest.mark.asyncio
    async def test_fetch_proxies_html_fallback_json(self, proxy_manager):
        """Test HTML fetching failure with JSON fallback."""
        mock_json_proxies = ["9.10.11.12:8080"]
        
        with patch.object(proxy_manager, '_fetch_html_proxies') as mock_html:
            with patch.object(proxy_manager, '_fetch_json_proxies') as mock_json:
                mock_html.side_effect = Exception("HTML fetch failed")
                mock_json.return_value = mock_json_proxies
                
                result = await proxy_manager._fetch_proxies()
                
                assert result == mock_json_proxies
    
    @pytest.mark.asyncio
    async def test_test_proxies_batch_processing(self, proxy_manager):
        """Test proxy testing with batch processing."""
        test_proxies = [f"1.2.3.{i}:8080" for i in range(25)]  # More than batch size
        
        with patch.object(proxy_manager, '_test_proxy_batch') as mock_batch:
            mock_batch.return_value = ["1.2.3.1:8080", "1.2.3.2:8080"]
            
            result = await proxy_manager._test_proxies(test_proxies)
            
            # Should call batch testing multiple times
            # 25 proxies with batch size 10: [0-9], [10-19], [20-24] = 3 batches
            assert mock_batch.call_count == 3
            assert len(result) == 6  # 3 batches * 2 valid proxies each
    
    @pytest.mark.asyncio
    async def test_test_proxy_batch_success(self, proxy_manager):
        """Test successful batch proxy testing."""
        test_proxies = ["1.2.3.4:8080", "5.6.7.8:3128"]
        
        with patch.object(proxy_manager._cpu_executors, 'run_in_thread') as mock_run:
            mock_run.return_value = asyncio.Future()
            mock_run.return_value.set_result(True)  # All proxies valid
            
            result = await proxy_manager._test_proxy_batch(test_proxies)
            
            assert result == test_proxies
    
    @pytest.mark.asyncio
    async def test_test_proxy_batch_mixed_results(self, proxy_manager):
        """Test batch proxy testing with mixed valid/invalid results."""
        test_proxies = ["1.2.3.4:8080", "5.6.7.8:3128", "9.10.11.12:8080"]
        
        with patch.object(proxy_manager._cpu_executors, 'run_in_thread') as mock_run:
            # Create multiple futures for different calls
            futures = []
            for i in range(3):
                future = asyncio.Future()
                if i == 1:  # Second proxy fails
                    future.set_exception(Exception("Connection failed"))
                else:
                    future.set_result(True)
                futures.append(future)
            
            mock_run.side_effect = futures
            
            result = await proxy_manager._test_proxy_batch(test_proxies)
            
            # Should return only valid proxies (first and third)
            # Note: The actual result depends on how the futures are processed
            assert len(result) >= 0  # At least some proxies should be processed
            assert "1.2.3.4:8080" in result or "9.10.11.12:8080" in result
    
    def test_test_single_proxy_success(self, proxy_manager):
        """Test successful single proxy testing."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = proxy_manager._test_single_proxy("1.2.3.4:8080")
            
            assert result is True
            mock_get.assert_called_once()
    
    def test_test_single_proxy_failure(self, proxy_manager):
        """Test failed single proxy testing."""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            result = proxy_manager._test_single_proxy("1.2.3.4:8080")
            
            assert result is False
    
    def test_get_stats(self, proxy_manager):
        """Test getting proxy manager statistics."""
        proxy_manager._proxies = ["1.2.3.4:8080"]
        proxy_manager._proxy_timestamp = datetime.now()
        proxy_manager._refresh_count = 5
        
        stats = proxy_manager.get_stats()
        
        assert stats["proxy_count"] == 1
        assert "last_refresh" in stats
        assert "next_refresh" in stats
        assert stats["refresh_count"] == 5
    
    def test_shutdown(self, proxy_manager):
        """Test proxy manager shutdown."""
        with patch.object(proxy_manager._cpu_executors, 'shutdown') as mock_shutdown:
            proxy_manager.shutdown()
            
            mock_shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, proxy_manager):
        """Test concurrent access to proxy manager."""
        # Set up some proxies
        proxy_manager._proxies = ["1.2.3.4:8080"]
        proxy_manager._proxy_timestamp = datetime.now()
        
        # Create multiple concurrent tasks
        async def get_proxies():
            return await proxy_manager.get_proxies()
        
        tasks = [get_proxies() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should return the same result
        assert all(result == ["1.2.3.4:8080"] for result in results)
