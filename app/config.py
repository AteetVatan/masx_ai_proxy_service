"""
Configuration settings for the MASX AI Proxy Service.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
        # Pydantic Settings to load .env file
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Proxy configuration
    proxy_webpage: str = Field(
        default="https://free-proxy-list.net/",
        description="URL to scrape proxies from"
    )
    proxy_testing_url: str = Field(
        default="https://httpbin.org/ip",
        description="URL to test proxy connectivity"
    )
    refresh_interval_minutes: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Proxy refresh interval in minutes"
    )
    proxy_test_timeout: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Proxy test timeout in seconds"
    )
    batch_size: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Number of proxies to test concurrently"
    )
    
    api_key: str = Field(default="", description="API key")
    require_api_key: bool = Field(default=False, description="Require API key")
    
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1024, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")
    
    # Rate limiting
    # max_refresh_requests_per_minute: int = Field(
    #     default=10,
    #     ge=1,
    #     le=100,
    #     description="Maximum refresh requests per minute"
    # )   



# Global settings instance
_settings = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
