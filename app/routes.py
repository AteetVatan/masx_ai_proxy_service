"""
FastAPI routes for the MASX AI Proxy Service.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.proxy_manager import ProxyManager
from app.logging_config import get_service_logger

# Initialize router
router = APIRouter(prefix="/api/v1", tags=["proxies"])
logger = get_service_logger("Routes")


# Response models
class ProxyResponse(BaseModel):
    """Response model for proxy endpoints."""
    success: bool
    data: Any
    message: str = "Success"


class RefreshResponse(BaseModel):
    """Response model for refresh endpoint."""
    success: bool
    proxy_count: int
    last_refresh: str = None
    next_refresh: str = None
    message: str = "Success"


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    message: str


@router.get("/proxies", response_model=ProxyResponse)
async def get_proxies():
    """
    Get all available valid proxies.
    
    Returns:
        List of working proxy strings in format "ip:port"
    """
    try:
        logger.info("GET /proxies endpoint called")
        proxies = await ProxyManager.proxies_async()
        
        return ProxyResponse(
            success=True,
            data=proxies,
            message=f"Retrieved {len(proxies)} valid proxies"
        )
        
    except Exception as e:
        logger.error(f"Error in get_proxies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve proxies: {str(e)}"
        )


@router.get("/proxy/random", response_model=ProxyResponse)
async def get_random_proxy():
    """
    Get a random valid proxy.
    
    Returns:
        Single proxy string in format "ip:port"
    """
    try:
        logger.info("GET /proxy/random endpoint called")
        proxy = ProxyManager.get_random_proxy()
        
        if not proxy:
            return ProxyResponse(
                success=False,
                data=None,
                message="No valid proxies available"
            )
        
        return ProxyResponse(
            success=True,
            data=proxy,
            message="Random proxy retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in get_random_proxy: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve random proxy: {str(e)}"
        )

@router.get("/stats", response_model=ProxyResponse)
async def get_stats():
    """
    Get proxy manager statistics.
    
    Returns:
        Statistics including proxy count, refresh timing, and rate limiting info
    """
    try:
        logger.info("GET /stats endpoint called")
        stats = ProxyManager.get_stats()
        
        return ProxyResponse(
            success=True,
            data=stats,
            message="Statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error in get_stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.get("/health", response_model=ProxyResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    try:
        logger.info("GET /health endpoint called")
        stats = ProxyManager.get_stats()
        
        health_status = {
            "status": "healthy",
            "proxy_count": stats["proxy_count"],
            "last_refresh": stats["last_refresh"],
            "service": "MASX AI Proxy Service"
        }
        
        return ProxyResponse(
            success=True,
            data=health_status,
            message="Service is healthy"
        )
        
    except Exception as e:
        logger.error(f"Error in health_check: {e}", exc_info=True)
        return ProxyResponse(
            success=False,
            data={"status": "unhealthy", "error": str(e)},
            message="Service health check failed"
        )
