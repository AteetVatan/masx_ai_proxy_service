#!/usr/bin/env python3
"""
🚀 MASX AI Proxy Service - Python Runner

A Python-based runner for the MASX AI Proxy Service that provides
an alternative to the Makefile while maintaining the same functionality.

This runner integrates with the Settings class from config.py to provide
consistent configuration management and validation.

Usage:
    python run.py                    # Run with default settings
    python run.py --port 8001       # Run on specific port
    python run.py --host 127.0.0.1  # Run on specific host
    python run.py --reload          # Enable auto-reload
    python run.py --help            # Show help
"""

import argparse
import os
import sys
import uvicorn
from pathlib import Path
from app.config import get_settings


def main():
    """Main entry point."""
    try:
        settings = get_settings()
        # Configure uvicorn settings
        uvicorn_config = {
            "app": "app.main:app",
            "host": settings.host,
            "port": settings.port,
            "reload": True,
            "access_log": True,
            "use_colors": True
        }
        
        # Remove None values
        uvicorn_config = {k: v for k, v in uvicorn_config.items() if v is not None}
        
        print("Starting MASX AI Proxy Service...")       
        # Start the server
        uvicorn.run(**uvicorn_config)
        
    except KeyboardInterrupt:
        print("Service stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting service: {e}")
        print("Check the logs above for more details")
        sys.exit(1)

if __name__ == "__main__":
    main()
