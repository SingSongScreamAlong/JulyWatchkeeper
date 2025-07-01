#!/usr/bin/env python

import os
import sys
import argparse
import logging
import uvicorn
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_argparse():
    parser = argparse.ArgumentParser(description='Run the WATCHKEEPER API server')
    parser.add_argument('--host', type=str, help='Host to bind the server to')
    parser.add_argument('--port', type=int, help='Port to bind the server to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = setup_argparse()
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment variables or command line arguments
    host = args.host or os.getenv("API_HOST", "0.0.0.0")
    port = args.port or int(os.getenv("API_PORT", 8000))
    reload = args.reload or os.getenv("API_DEBUG", "false").lower() == "true"
    debug = args.debug or os.getenv("API_DEBUG", "false").lower() == "true"
    
    # Set log level based on debug mode
    log_level = "debug" if debug else os.getenv("LOG_LEVEL", "info").lower()
    
    # Log configuration
    logger.info(f"Starting WATCHKEEPER API server")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Reload: {reload}")
    logger.info(f"Debug: {debug}")
    logger.info(f"Log level: {log_level}")
    
    # Run the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )

if __name__ == "__main__":
    main()
