"""
Main FastAPI application for the MASX AI Proxy Service.
"""

import asyncio
import signal
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


from app.config import get_settings
from app.logging_config import get_service_logger, configure_logging
from app.routes import router
from app.proxy_manager import ProxyManager

# Global task reference
proxy_task: asyncio.Task | None = None

# Configure logging
settings = get_settings()
configure_logging(settings.log_level, settings.log_format)
logger = get_service_logger("Main")


async def verify_api_key(request: Request):
    """
    Verify API key from request headers.

    Args:
        request: FastAPI request object

    Returns:
        bool: True if API key is valid

    Raises:
        HTTPException: If API key is missing or invalid
    """
    settings = get_settings()

    # Skip verification if not required
    if not settings.require_api_key:
        return True

    # Get API key from headers
    api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization")

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide X-API-Key or Authorization header",
        )

    # Remove 'Bearer ' prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]

    # Verify against configured API key
    if api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return True


# Create FastAPI app
app = FastAPI(
    title="MASX AI Proxy Service",
    description="A FastAPI service for managing and validating free proxies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    dependencies=[Depends(verify_api_key)] if settings.require_api_key else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
        
# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}",
                 path=request.url.path,
                 method=request.method)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.error(f"Validation error: {exc.errors()}",
                 path=request.url.path,
                 method=request.method)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}",
                 path=request.url.path,
                 method=request.method,
                 exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


# Include routes
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "MASX AI Proxy Service",
        "version": "1.0.0",
        "description": "A FastAPI service for managing and validating free proxies",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/api/v1/health",
            "proxies": "/api/v1/proxies",
            "random_proxy": "/api/v1/proxy/random",
            "start_refresh": "/start-refresh",
            "stats": "/api/v1/stats"
        }
    }
    
@app.post("/shutdown")
async def shutdown(request: Request):
    """Gracefully shutdown FastAPI server."""
    # Works with Uvicorn
    pid = os.getpid()
    os.kill(pid, signal.SIGINT)  # or SIGTERM for docker
    return {"message": "Shutdown signal sent"}

async def refresh_proxies_periodically(run_time: int = 7200):
    """Refresh proxies every 5 minutes, stop after run_time seconds."""
    start_time = asyncio.get_event_loop().time()
    while True:
        if asyncio.get_event_loop().time() - start_time > run_time:
            logger.info("Proxy refresher reached 2h limit, stopping task.")
            break
        try:
            logger.info("Refreshing proxies (scheduled task)")
            await ProxyManager.refresh_proxies()
        except Exception as e:
            logger.error(f"Error in refresh_proxies_periodically: {e}")
        await asyncio.sleep(300)  # 5 minutes
        
@app.post("/api/v1/start-refresh")
async def start_refresh(run_time: int = 7200):
    """Start the proxy refresher (default 2h)."""
    global proxy_task
    if proxy_task is None or proxy_task.done():
        proxy_task = asyncio.create_task(refresh_proxies_periodically(run_time))
        return {"status": "started", "duration": f"{run_time//3600} hours"}
    return {"status": "already running"}

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
