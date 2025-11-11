#!/usr/bin/env python3
"""
Test a specific intelligence source

Usage: python test_source.py "Source Name"
"""

import sys
import json
import asyncio
import aiohttp
import feedparser
from pathlib import Path
from datetime import datetime

async def test_source(source_name: str):
    """Test if a source is accessible and returning data."""

    # Load sources
    config_dir = Path(__file__).parent.parent / "config"
    sources_file = config_dir / "sources.json"

    with open(sources_file, 'r') as f:
        config = json.load(f)

    # Find source
    source = None
    for s in config["sources"]:
        if s["name"].lower() == source_name.lower():
            source = s
            break

    if not source:
        print(f"❌ Source not found: {source_name}")
        print(f"\nAvailable sources:")
        for s in config["sources"][:10]:
            print(f"  - {s['name']}")
        print(f"  ... and {len(config['sources']) - 10} more")
        return False

    print(f"{'='*60}")
    print(f"Testing Source: {source['name']}")
    print(f"{'='*60}")
    print(f"URL:        {source['url']}")
    print(f"Type:       {source['type']}")
    print(f"Category:   {source.get('category', 'N/A')}")
    print(f"Reliability: {source.get('reliability', 'N/A')}/10")
    print(f"Enabled:    {source.get('enabled', True)}")
    print(f"{'='*60}\n")

    # Test connection
    print("🔍 Testing connection...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(source['url'], timeout=10) as response:
                status = response.status
                content_type = response.headers.get('Content-Type', 'unknown')

                if status == 200:
                    print(f"✓ Connection successful (HTTP {status})")
                    print(f"  Content-Type: {content_type}")

                    # Try to parse as RSS/Atom
                    if source['type'] in ['rss', 'atom']:
                        content = await response.text()
                        feed = feedparser.parse(content)

                        if feed.entries:
                            print(f"\n✓ Feed parsed successfully")
                            print(f"  Title: {feed.feed.get('title', 'N/A')}")
                            print(f"  Entries: {len(feed.entries)}")

                            # Show first 3 entries
                            print(f"\n  Recent entries:")
                            for i, entry in enumerate(feed.entries[:3], 1):
                                title = entry.get('title', 'No title')
                                published = entry.get('published', 'No date')
                                print(f"    {i}. {title[:60]}...")
                                print(f"       Published: {published}")

                            print(f"\n✓ Source is WORKING correctly!")
                            return True
                        else:
                            print(f"⚠️  Feed parsed but contains no entries")
                            return False
                    else:
                        print(f"✓ Connection successful, content received")
                        return True
                else:
                    print(f"❌ Connection failed (HTTP {status})")
                    return False

    except asyncio.TimeoutError:
        print(f"❌ Connection timeout (>10 seconds)")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_source.py \"Source Name\"")
        print("\nExamples:")
        print("  python test_source.py \"Open Doors USA\"")
        print("  python test_source.py \"BBC Europe\"")
        sys.exit(1)

    source_name = sys.argv[1]
    success = asyncio.run(test_source(source_name))
    sys.exit(0 if success else 1)
