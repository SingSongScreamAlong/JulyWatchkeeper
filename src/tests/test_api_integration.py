"""
Test API Integration for WATCHKEEPER

This script tests the integration of the WATCHKEEPER API components:
1. REST API endpoints
2. WebSocket real-time updates
3. Redis caching
"""

import os
import sys
import json
import asyncio
import argparse
import aiohttp
import websockets
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.logger import get_logger
from src.utils.config import load_config

# Initialize logger
logger = get_logger("watchkeeper.tests.api_integration")

# Sample intelligence item for testing
SAMPLE_INTELLIGENCE = {
    "title": "Peaceful Protests Continue in Capital City",
    "content": "Peaceful demonstrations continued for the third day in the capital city. Protesters are demanding political reforms, but no violence has been reported. Police presence remains minimal, and businesses are operating normally.",
    "source": {
        "name": "news.bbc",
        "type": "news",
        "reliability": 0.9
    },
    "url": "https://example.com/news/peaceful-protests",
    "published_date": datetime.now().isoformat(),
    "language": "en",
    "locations": ["Capital City"],
    "tags": ["protest", "peaceful", "political"]
}

class APITester:
    """
    API Integration Tester
    
    Tests the integration of REST API, WebSocket, and Redis cache.
    """
    
    def __init__(self, api_base_url: str, ws_base_url: str):
        """
        Initialize the API tester
        
        Args:
            api_base_url: Base URL for REST API
            ws_base_url: Base URL for WebSocket
        """
        self.api_base_url = api_base_url
        self.ws_base_url = ws_base_url
        self.session = None
        self.ws = None
        self.client_id = f"test-client-{datetime.now().timestamp()}"
        self.ws_messages = []
        self.item_id = None
    
    async def setup(self):
        """Set up the test environment"""
        self.session = aiohttp.ClientSession()
        logger.info("Test session initialized")
    
    async def teardown(self):
        """Clean up the test environment"""
        if self.session:
            await self.session.close()
        
        if self.ws:
            await self.ws.close()
        
        logger.info("Test session closed")
    
    async def test_api_root(self) -> bool:
        """
        Test the API root endpoint
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with self.session.get(f"{self.api_base_url}/") as response:
                if response.status != 200:
                    logger.error(f"API root endpoint returned status {response.status}")
                    return False
                
                data = await response.json()
                
                if data.get("status") != "success":
                    logger.error(f"API root endpoint returned error: {data}")
                    return False
                
                logger.info("API root endpoint test passed")
                return True
        
        except Exception as e:
            logger.error(f"Error testing API root endpoint: {e}", exc_info=True)
            return False
    
    async def test_submit_intelligence(self) -> bool:
        """
        Test submitting intelligence
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with self.session.post(
                f"{self.api_base_url}/intelligence",
                json=SAMPLE_INTELLIGENCE
            ) as response:
                if response.status != 200:
                    logger.error(f"Submit intelligence endpoint returned status {response.status}")
                    return False
                
                data = await response.json()
                
                if data.get("status") != "success":
                    logger.error(f"Submit intelligence endpoint returned error: {data}")
                    return False
                
                logger.info("Submit intelligence test passed")
                return True
        
        except Exception as e:
            logger.error(f"Error testing submit intelligence endpoint: {e}", exc_info=True)
            return False
    
    async def test_process_intelligence(self) -> bool:
        """
        Test processing intelligence
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with self.session.post(
                f"{self.api_base_url}/process",
                json=SAMPLE_INTELLIGENCE
            ) as response:
                if response.status != 200:
                    logger.error(f"Process intelligence endpoint returned status {response.status}")
                    return False
                
                data = await response.json()
                
                if data.get("status") != "success":
                    logger.error(f"Process intelligence endpoint returned error: {data}")
                    return False
                
                # Check that the response contains processed data
                processed_item = data.get("data", {})
                
                if not processed_item.get("ai_analysis"):
                    logger.error("Processed item does not contain AI analysis")
                    return False
                
                if not processed_item.get("geo_data"):
                    logger.error("Processed item does not contain geographic data")
                    return False
                
                if not processed_item.get("severity_assessment"):
                    logger.error("Processed item does not contain severity assessment")
                    return False
                
                if not processed_item.get("relevance_assessment"):
                    logger.error("Processed item does not contain relevance assessment")
                    return False
                
                logger.info("Process intelligence test passed")
                return True
        
        except Exception as e:
            logger.error(f"Error testing process intelligence endpoint: {e}", exc_info=True)
            return False
    
    async def test_list_intelligence(self) -> bool:
        """
        Test listing intelligence
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with self.session.get(
                f"{self.api_base_url}/intelligence?limit=10"
            ) as response:
                if response.status != 200:
                    logger.error(f"List intelligence endpoint returned status {response.status}")
                    return False
                
                data = await response.json()
                
                if data.get("status") != "success":
                    logger.error(f"List intelligence endpoint returned error: {data}")
                    return False
                
                logger.info("List intelligence test passed")
                return True
        
        except Exception as e:
            logger.error(f"Error testing list intelligence endpoint: {e}", exc_info=True)
            return False
    
    async def test_search_intelligence(self) -> bool:
        """
        Test searching intelligence
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            search_query = {
                "query": "protest",
                "limit": 10
            }
            
            async with self.session.post(
                f"{self.api_base_url}/search",
                json=search_query
            ) as response:
                if response.status != 200:
                    logger.error(f"Search intelligence endpoint returned status {response.status}")
                    return False
                
                data = await response.json()
                
                if data.get("status") != "success":
                    logger.error(f"Search intelligence endpoint returned error: {data}")
                    return False
                
                logger.info("Search intelligence test passed")
                return True
        
        except Exception as e:
            logger.error(f"Error testing search intelligence endpoint: {e}", exc_info=True)
            return False
    
    async def test_system_status(self) -> bool:
        """
        Test system status endpoint
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            async with self.session.get(
                f"{self.api_base_url}/status"
            ) as response:
                if response.status != 200:
                    logger.error(f"System status endpoint returned status {response.status}")
                    return False
                
                data = await response.json()
                
                if data.get("status") != "success":
                    logger.error(f"System status endpoint returned error: {data}")
                    return False
                
                # Check that the response contains status information
                status_data = data.get("data", {})
                
                if not status_data.get("processors"):
                    logger.error("Status data does not contain processor information")
                    return False
                
                if not status_data.get("storage"):
                    logger.error("Status data does not contain storage information")
                    return False
                
                logger.info("System status test passed")
                return True
        
        except Exception as e:
            logger.error(f"Error testing system status endpoint: {e}", exc_info=True)
            return False
    
    async def test_websocket_connection(self) -> bool:
        """
        Test WebSocket connection
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Connect to WebSocket
            self.ws = await websockets.connect(f"{self.ws_base_url}/ws/{self.client_id}")
            
            # Send a ping message
            await self.ws.send(json.dumps({
                "type": "ping"
            }))
            
            # Wait for response
            response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") != "pong":
                logger.error(f"WebSocket ping test failed: {data}")
                return False
            
            logger.info("WebSocket connection test passed")
            return True
        
        except Exception as e:
            logger.error(f"Error testing WebSocket connection: {e}", exc_info=True)
            return False
    
    async def test_websocket_subscription(self) -> bool:
        """
        Test WebSocket subscription
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Subscribe to intelligence updates
            await self.ws.send(json.dumps({
                "type": "subscribe",
                "topic": "intelligence"
            }))
            
            # Wait for response
            response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") != "subscription" or data.get("status") != "success":
                logger.error(f"WebSocket subscription test failed: {data}")
                return False
            
            # Subscribe to system updates
            await self.ws.send(json.dumps({
                "type": "subscribe",
                "topic": "system"
            }))
            
            # Wait for response
            response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)
            data = json.loads(response)
            
            if data.get("type") != "subscription" or data.get("status") != "success":
                logger.error(f"WebSocket subscription test failed: {data}")
                return False
            
            logger.info("WebSocket subscription test passed")
            return True
        
        except Exception as e:
            logger.error(f"Error testing WebSocket subscription: {e}", exc_info=True)
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """
        Run all integration tests
        
        Returns:
            Dict[str, bool]: Test results
        """
        await self.setup()
        
        results = {
            "api_root": await self.test_api_root(),
            "submit_intelligence": await self.test_submit_intelligence(),
            "process_intelligence": await self.test_process_intelligence(),
            "list_intelligence": await self.test_list_intelligence(),
            "search_intelligence": await self.test_search_intelligence(),
            "system_status": await self.test_system_status(),
            "websocket_connection": await self.test_websocket_connection(),
            "websocket_subscription": await self.test_websocket_subscription()
        }
        
        await self.teardown()
        
        return results

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test API integration")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000", help="API base URL")
    parser.add_argument("--ws-url", type=str, default="ws://localhost:8000", help="WebSocket base URL")
    args = parser.parse_args()
    
    # Load configuration
    load_config(args.config)
    
    # Create API tester
    tester = APITester(args.api_url, args.ws_url)
    
    # Run tests
    results = await tester.run_all_tests()
    
    # Print results
    print("\n===== API Integration Test Results =====")
    
    all_passed = True
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        if not result:
            all_passed = False
        print(f"{test_name}: {status}")
    
    print("\nOverall result:", "✓ PASSED" if all_passed else "✗ FAILED")
    
    # Return exit code
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
