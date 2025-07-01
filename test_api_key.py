#!/usr/bin/env python3
"""
API Key Debugging Script

This script tests the API key handling in the WATCHKEEPER API.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("API_KEY", "watchkeeper_secure_api_key_2025")
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")

# Print debugging information
print("=== API Key Debugging Information ===")
print(f"API_KEY from environment: {API_KEY}")
print(f"API_HOST from environment: {API_HOST}")
print(f"API_PORT from environment: {API_PORT}")

# Test with different header configurations
headers_to_test = [
    {"X-API-Key": API_KEY},
    {"x-api-key": API_KEY},  # Test case sensitivity
    {"Authorization": f"Bearer {API_KEY}"},  # Test alternative format
    {"api-key": API_KEY},  # Test different format
    {"API_KEY": API_KEY}  # Test different format
]

for i, headers in enumerate(headers_to_test):
    print(f"\nTest {i+1}: Using headers: {headers}")
    try:
        response = requests.get(
            f"http://{API_HOST}:{API_PORT}/api/v1/intelligence",
            headers=headers
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
