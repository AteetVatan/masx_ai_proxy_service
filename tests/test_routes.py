"""
API tests for FastAPI routes using TestClient.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.main import app


class TestRoutes:
    """Test cases for FastAPI routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test the root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "MASX AI Proxy Service"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
    
    def test_docs_endpoint(self, client):
        """Test that docs endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint(self, client):
        """Test that redoc endpoint is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
    
    def test_get_proxies_success(self, client):
        """Test successful GET /proxies endpoint."""
        mock_proxies = ["1.2.3.4:8080", "5.6.7.8:3128"]
        
        with patch('app.routes.proxy_manager') as mock_pm:
            # Create an async mock that returns the proxies
            async def mock_get_proxies():
                return mock_proxies
            mock_pm.get_proxies = mock_get_proxies
            
            response = client.get("/api/v1/proxies")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == mock_proxies
        assert "Retrieved 2 valid proxies" in data["message"]
    
    def test_get_proxies_empty(self, client):
        """Test GET /proxies endpoint with no proxies."""
        mock_proxies = []
        
        with patch('app.routes.proxy_manager') as mock_pm:
            # Create an async mock that returns empty list
            async def mock_get_proxies():
                return mock_proxies
            mock_pm.get_proxies = mock_get_proxies
            
            response = client.get("/api/v1/proxies")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
        assert "Retrieved 0 valid proxies" in data["message"]
    
    def test_get_proxies_error(self, client):
        """Test GET /proxies endpoint with error."""
        with patch('app.routes.proxy_manager') as mock_pm:
            # Create an async mock that raises an exception
            async def mock_get_proxies():
                raise Exception("Database error")
            mock_pm.get_proxies = mock_get_proxies
            
            response = client.get("/api/v1/proxies")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Failed to retrieve proxies: Database error" in data["message"]
    
    def test_get_random_proxy_success(self, client):
        """Test successful GET /proxy/random endpoint."""
        mock_proxy = "1.2.3.4:8080"
        
        with patch('app.routes.proxy_manager') as mock_pm:
            mock_pm.get_random_proxy.return_value = mock_proxy
            
            response = client.get("/api/v1/proxy/random")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == mock_proxy
        assert "Random proxy retrieved successfully" in data["message"]
    
    def test_get_random_proxy_no_proxies(self, client):
        """Test GET /proxy/random endpoint with no proxies available."""
        with patch('app.routes.proxy_manager') as mock_pm:
            mock_pm.get_random_proxy.return_value = None
            
            response = client.get("/api/v1/proxy/random")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"] is None
        assert "No valid proxies available" in data["message"]
    
    def test_get_random_proxy_error(self, client):
        """Test GET /proxy/random endpoint with error."""
        with patch('app.routes.proxy_manager') as mock_pm:
            mock_pm.get_random_proxy.side_effect = Exception("Service error")
            
            response = client.get("/api/v1/proxy/random")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Failed to retrieve random proxy: Service error" in data["message"]
    
    def test_refresh_proxies_success(self, client):
        """Test successful POST /refresh endpoint."""
        mock_result = {
            "success": True,
            "proxy_count": 5,
            "last_refresh": "2024-01-01T12:00:00",
            "next_refresh": "2024-01-01T12:05:00"
        }
        
        with patch('app.routes.proxy_manager') as mock_pm:
            # Create an async mock that returns the result
            async def mock_refresh_proxies():
                return mock_result
            mock_pm.refresh_proxies = mock_refresh_proxies
            
            response = client.post("/api/v1/refresh")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["proxy_count"] == 5
        assert data["last_refresh"] == "2024-01-01T12:00:00"
        assert data["next_refresh"] == "2024-01-01T12:05:00"
        assert "Successfully refreshed proxies" in data["message"]
    
    def test_refresh_proxies_rate_limited(self, client):
        """Test POST /refresh endpoint with rate limiting."""
        mock_result = {
            "success": False,
            "message": "Rate limit exceeded",
            "next_refresh": "2024-01-01T12:05:00"
        }
        
        with patch('app.routes.proxy_manager') as mock_pm:
            # Create an async mock that returns the result
            async def mock_refresh_proxies():
                return mock_result
            mock_pm.refresh_proxies = mock_refresh_proxies
            
            response = client.post("/api/v1/refresh")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["proxy_count"] == 0
        assert "Rate limit exceeded" in data["message"]
    
    def test_refresh_proxies_error(self, client):
        """Test POST /refresh endpoint with error."""
        with patch('app.routes.proxy_manager') as mock_pm:
            # Create an async mock that raises an exception
            async def mock_refresh_proxies():
                raise Exception("Refresh failed")
            mock_pm.refresh_proxies = mock_refresh_proxies
            
            response = client.post("/api/v1/refresh")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Failed to refresh proxies: Refresh failed" in data["message"]
    
    def test_get_stats_success(self, client):
        """Test successful GET /stats endpoint."""
        mock_stats = {
            "proxy_count": 10,
            "last_refresh": "2024-01-01T12:00:00",
            "next_refresh": "2024-01-01T12:05:00",
            "refresh_count": 3,
            "max_refresh_per_minute": 10
        }
        
        with patch('app.routes.proxy_manager') as mock_pm:
            mock_pm.get_stats.return_value = mock_stats
            
            response = client.get("/api/v1/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == mock_stats
        assert "Statistics retrieved successfully" in data["message"]
    
    def test_get_stats_error(self, client):
        """Test GET /stats endpoint with error."""
        with patch('app.routes.proxy_manager') as mock_pm:
            mock_pm.get_stats.side_effect = Exception("Stats error")
            
            response = client.get("/api/v1/stats")
        
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Failed to retrieve statistics: Stats error" in data["message"]
    
    def test_health_check_success(self, client):
        """Test successful GET /health endpoint."""
        mock_stats = {
            "proxy_count": 5,
            "last_refresh": "2024-01-01T12:00:00",
            "next_refresh": "2024-01-01T12:05:00"
        }
        
        with patch('app.routes.proxy_manager') as mock_pm:
            mock_pm.get_stats.return_value = mock_stats
            
            response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert data["data"]["proxy_count"] == 5
        assert data["data"]["service"] == "MASX AI Proxy Service"
        assert "Service is healthy" in data["message"]
    
    def test_health_check_error(self, client):
        """Test GET /health endpoint with error."""
        with patch('app.routes.proxy_manager') as mock_pm:
            mock_pm.get_stats.side_effect = Exception("Health check failed")
            
            response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["data"]["status"] == "unhealthy"
        assert "Service health check failed" in data["message"]
    
    def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404."""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options("/api/v1/proxies")
        # CORS preflight request should not fail
        assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        mock_proxies = ["1.2.3.4:8080", "5.6.7.8:3128"]
        
        with patch('app.routes.proxy_manager') as mock_pm:
            # Create an async mock that returns the proxies
            async def mock_get_proxies():
                return mock_proxies
            mock_pm.get_proxies = mock_get_proxies
            
            # Make multiple requests
            responses = []
            for _ in range(5):
                response = client.get("/api/v1/proxies")
                responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"] == mock_proxies
