#!/usr/bin/env python3
"""
WATCHKEEPER - System Test
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

async def test_components():
    print("🧪 WATCHKEEPER - System Test")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Import dependencies
    total_tests += 1
    try:
        import playwright
        import nltk
        import feedparser
        import aiohttp
        import sqlite3
        print("✅ Test 1: All Python dependencies imported")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ Test 1: Missing dependency: {e}")
    
    # Test 2: NLTK data
    total_tests += 1
    try:
        from nltk.sentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        test_sentiment = analyzer.polarity_scores("This is a test")
        print("✅ Test 2: NLTK sentiment analysis working")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2: NLTK sentiment analysis failed: {e}")
    
    # Test 3: Playwright browser
    total_tests += 1
    try:
        from playwright.async_api import async_playwright
        playwright_instance = await async_playwright().start()
        browser = await playwright_instance.chromium.launch(headless=True)
        await browser.close()
        await playwright_instance.stop()
        print("✅ Test 3: Playwright browser working")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3: Playwright browser failed: {e}")
    
    # Test 4: Database creation
    total_tests += 1
    try:
        import sqlite3
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test (id INTEGER)")
        conn.close()
        print("✅ Test 4: SQLite database working")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4: SQLite database failed: {e}")
    
    # Test 5: RSS feed parsing
    total_tests += 1
    try:
        import feedparser
        feed = feedparser.parse("https://feeds.bbci.co.uk/news/world/rss.xml")
        if feed.entries:
            print("✅ Test 5: RSS feed parsing working")
            tests_passed += 1
        else:
            print("❌ Test 5: RSS feed parsing - no entries found")
    except Exception as e:
        print(f"❌ Test 5: RSS feed parsing failed: {e}")
    
    # Test 6: Configuration files
    total_tests += 1
    try:
        config_path = Path("config/settings.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            print("✅ Test 6: Configuration files present")
            tests_passed += 1
        else:
            print("❌ Test 6: Configuration files missing")
    except Exception as e:
        print(f"❌ Test 6: Configuration files failed: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! WATCHKEEPER is ready to run.")
        return True
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_components())
    sys.exit(0 if result else 1)
