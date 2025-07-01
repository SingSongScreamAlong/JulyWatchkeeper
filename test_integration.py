#!/usr/bin/env python3
"""
WatchKeeper-Sentinel Integration Test Script

This script tests the complete integration flow between WatchKeeper and Sentinel:
1. API authentication
2. Intelligence data sending via API
3. WebSocket real-time updates
4. File-based integration
"""

import os
import sys
import json
import time
import asyncio
import logging
import sqlite3
import requests
import websockets
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8000")
API_KEY = os.getenv("API_KEY", "watchkeeper_secure_api_key_2025")
WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "localhost")
WEBSOCKET_PORT = os.getenv("WEBSOCKET_PORT", "8000")
SENTINEL_API_ENDPOINT = os.getenv("SENTINEL_API_ENDPOINT", "http://localhost:8080/api/v1/intelligence")
SENTINEL_API_KEY = os.getenv("SENTINEL_API_KEY", "sentinel_integration_key_2025")

# Test data
TEST_INTELLIGENCE_ITEM = {
    "title": "Test Intelligence Item",
    "content": "This is a test intelligence item for integration testing",
    "summary": "Test intelligence for integration",
    "source": "Integration Test",
    "source_id": 999,  # Changed to integer
    "raw_content": "This is the raw content of the test intelligence item for integration testing.",
    "url": "https://example.com/test",
    "collection_date": datetime.now().isoformat(),
    "publication_date": datetime.now().isoformat(),
    "threat_level": 5.0,
    "missionary_relevance": 7.0,
    "region": "Test Region",
    "country": "Test Country",
    "location": "Test Location",
    "latitude": 0.0,
    "longitude": 0.0,
    "sentiment": 0.5,
    "confidence": 0.9
}

async def test_api_authentication():
    """Test API authentication"""
    logger.info("Testing API authentication...")
    
    # Test with valid API key
    try:
        response = requests.get(
            f"http://{API_HOST}:{API_PORT}/api/v1/intelligence",
            headers={"X-API-Key": API_KEY}
        )
        if response.status_code == 200:
            logger.info("✅ API authentication successful")
        else:
            logger.error(f"❌ API authentication failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ API authentication failed: {e}")
        return False
    
    # Test with invalid API key
    try:
        response = requests.get(
            f"http://{API_HOST}:{API_PORT}/api/v1/intelligence",
            headers={"X-API-Key": "invalid_key"}
        )
        if response.status_code == 401:
            logger.info("✅ API authentication correctly rejected invalid key")
        else:
            logger.warning(f"⚠️ API authentication did not reject invalid key: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ API authentication test failed: {e}")
    
    return True

async def test_api_integration():
    """Test sending intelligence data via API"""
    logger.info("Testing API integration...")
    
    try:
        # Create a test intelligence item
        response = requests.post(
            f"http://{API_HOST}:{API_PORT}/api/v1/intelligence",
            headers={"X-API-Key": API_KEY},
            json=TEST_INTELLIGENCE_ITEM
        )
        
        if response.status_code == 201:
            item_id = response.json().get("id")
            logger.info(f"✅ Created test intelligence item with ID: {item_id}")
        else:
            logger.error(f"❌ Failed to create test intelligence item: {response.status_code} - {response.text}")
            return False
        
        # Verify the item was created
        response = requests.get(
            f"http://{API_HOST}:{API_PORT}/api/v1/intelligence/{item_id}",
            headers={"X-API-Key": API_KEY}
        )
        
        if response.status_code == 200:
            logger.info("✅ Successfully retrieved test intelligence item")
        else:
            logger.error(f"❌ Failed to retrieve test intelligence item: {response.status_code} - {response.text}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ API integration test failed: {e}")
        return False

async def test_websocket_integration():
    """Test WebSocket real-time updates"""
    logger.info("Testing WebSocket integration...")
    
    try:
        # Connect to WebSocket server with client_id and API key in URL
        client_id = f"test_client_{int(time.time())}"
        uri = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/ws/{client_id}?api_key={API_KEY}"
        logger.info(f"Connecting to WebSocket server at {uri}...")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket server")
            
            # Subscribe to intelligence updates
            await websocket.send(json.dumps({
                "type": "subscribe",
                "topic": "intelligence"
            }))
            
            # Wait for subscription confirmation
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if response_data.get("status") == "success":
                logger.info("✅ Successfully subscribed to intelligence updates")
            else:
                logger.error(f"❌ Failed to subscribe to intelligence updates: {response_data}")
                return False
            
            # Create a new intelligence item to trigger an update
            new_item = TEST_INTELLIGENCE_ITEM.copy()
            new_item["title"] = "WebSocket Test Item"
            new_item["collection_date"] = datetime.now().isoformat()
            
            response = requests.post(
                f"http://{API_HOST}:{API_PORT}/api/v1/intelligence",
                headers={"X-API-Key": API_KEY},
                json=new_item
            )
            
            if response.status_code == 201:
                item_id = response.json().get("id")
                logger.info(f"✅ Created WebSocket test item with ID: {item_id}")
            else:
                logger.error(f"❌ Failed to create WebSocket test item: {response.status_code} - {response.text}")
                return False
            
            # Wait for WebSocket update
            logger.info("Waiting for WebSocket update...")
            try:
                # Set a timeout for receiving the message
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                if response_data.get("topic") == "intelligence":
                    logger.info("✅ Received WebSocket update for new intelligence item")
                    return True
                else:
                    logger.warning(f"⚠️ Received WebSocket message on unexpected topic: {response_data}")
            except asyncio.TimeoutError:
                logger.error("❌ Timed out waiting for WebSocket update")
                return False
            
        return True
    except Exception as e:
        logger.error(f"❌ WebSocket integration test failed: {e}")
        return False

def test_file_based_integration():
    """Test file-based integration"""
    logger.info("Testing file-based integration...")
    
    try:
        # Check if mission_intelligence.json exists
        dashboard_data_path = os.path.join("dashboard", "data", "mission_intelligence.json")
        if os.path.exists(dashboard_data_path):
            with open(dashboard_data_path, "r") as f:
                data = json.load(f)
                if data:
                    logger.info(f"✅ Found dashboard data file with {len(data.get('items', []))} intelligence items")
                else:
                    logger.warning("⚠️ Dashboard data file exists but contains no data")
        else:
            logger.warning(f"⚠️ Dashboard data file not found at {dashboard_data_path}")
        
        # Check if any HTML reports exist
        report_files = [f for f in os.listdir(os.path.join("dashboard", "data")) if f.startswith("report_") and f.endswith(".html")]
        if report_files:
            logger.info(f"✅ Found {len(report_files)} HTML report files")
        else:
            logger.warning("⚠️ No HTML report files found")
        
        return True
    except Exception as e:
        logger.error(f"❌ File-based integration test failed: {e}")
        return False

async def test_sentinel_api():
    """Test Sentinel API integration"""
    logger.info("Testing Sentinel API integration...")
    
    try:
        # Check if Sentinel API is accessible
        response = requests.get(
            SENTINEL_API_ENDPOINT,
            headers={"Authorization": f"Bearer {SENTINEL_API_KEY}"}
        )
        
        if response.status_code == 200:
            logger.info("✅ Sentinel API is accessible")
        else:
            logger.warning(f"⚠️ Sentinel API returned unexpected status code: {response.status_code}")
        
        # Send test data to Sentinel API
        test_data = {
            "items": [TEST_INTELLIGENCE_ITEM],
            "metadata": {
                "sender": "Integration Test",
                "timestamp": datetime.now().isoformat(),
                "total_items": 1
            }
        }
        
        response = requests.post(
            SENTINEL_API_ENDPOINT,
            headers={
                "Authorization": f"Bearer {SENTINEL_API_KEY}",
                "Content-Type": "application/json"
            },
            json=test_data
        )
        
        if response.status_code in [200, 201]:
            logger.info("✅ Successfully sent test data to Sentinel API")
            return True
        else:
            logger.warning(f"⚠️ Sentinel API returned unexpected status code: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ Could not connect to Sentinel API. Is the test interface running?")
        return False
    except Exception as e:
        logger.error(f"❌ Sentinel API integration test failed: {e}")
        return False

async def run_tests():
    """Run all integration tests"""
    logger.info("Starting WatchKeeper-Sentinel integration tests...")
    
    results = {
        "api_authentication": await test_api_authentication(),
        "api_integration": await test_api_integration(),
        "websocket_integration": await test_websocket_integration(),
        "file_based_integration": test_file_based_integration(),
        "sentinel_api": await test_sentinel_api()
    }
    
    # Print summary
    logger.info("\n=== Integration Test Summary ===")
    all_passed = True
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        if not result:
            all_passed = False
        logger.info(f"{status} - {test}")
    
    if all_passed:
        logger.info("\n🎉 All integration tests passed! WatchKeeper-Sentinel integration is working correctly.")
    else:
        logger.warning("\n⚠️ Some integration tests failed. Please check the logs for details.")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_tests())
