#!/usr/bin/env python3
"""
API Server Debugging Script

This script inspects the FastAPI application configuration and environment variables
to diagnose API authentication issues.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Print environment variables
print("=== Environment Variables ===")
print(f"API_KEY: {os.getenv('API_KEY')}")
print(f"API_HOST: {os.getenv('API_HOST')}")
print(f"API_PORT: {os.getenv('API_PORT')}")
print(f"PYTHONPATH: {os.getenv('PYTHONPATH')}")

# Try to import settings from the application
try:
    print("\n=== Attempting to import settings ===")
    sys.path.insert(0, os.getcwd())
    from src.core.config import settings
    
    print("\n=== Application Settings ===")
    print(f"API_KEY_HEADER: {settings.API_KEY_HEADER}")
    print(f"API_KEY: {settings.API_KEY}")
    print(f"SECRET_KEY: {settings.SECRET_KEY}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    
    # Check if API_KEY from environment matches settings
    env_api_key = os.getenv('API_KEY')
    if env_api_key and env_api_key == settings.API_KEY:
        print("\n✅ API_KEY from environment matches settings.API_KEY")
    else:
        print("\n❌ API_KEY from environment does NOT match settings.API_KEY")
        print(f"Environment: {env_api_key}")
        print(f"Settings: {settings.API_KEY}")
    
    # Test API key validation function
    try:
        print("\n=== Testing API key validation ===")
        from src.core.security import get_api_key
        
        # This is a simplified test - the actual function is async and uses FastAPI dependencies
        print("Note: This is a simplified test of the validation logic")
        if env_api_key == settings.API_KEY:
            print("✅ API key validation would pass with current environment value")
        else:
            print("❌ API key validation would fail with current environment value")
    
    except ImportError as e:
        print(f"Could not import get_api_key function: {e}")

except ImportError as e:
    print(f"Could not import settings: {e}")
    print("Make sure you're running this script from the project root directory.")

# Print system information
print("\n=== System Information ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Suggest next steps
print("\n=== Suggested Next Steps ===")
print("1. Ensure the API server is using the correct .env file")
print("2. Verify that settings.API_KEY matches the value in .env")
print("3. Check that the FastAPI dependency is correctly configured")
print("4. Restart the API server after any configuration changes")
