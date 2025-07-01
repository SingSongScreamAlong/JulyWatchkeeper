#!/usr/bin/env python3
"""
Start the WatchKeeper API Server
"""
import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import uvicorn
from dotenv import load_dotenv

def main():
    """Run the WatchKeeper API server"""
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Start the WatchKeeper API server")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the API server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the API server to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    
    args = parser.parse_args()
    
    print(f"Starting WatchKeeper API server on {args.host}:{args.port}")
    print("API documentation will be available at http://localhost:{args.port}/docs")
    
    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
