#!/usr/bin/env python3
"""
Real European Intelligence Collector
Collects real-time intelligence data from European news sources
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

# European news sources
EUROPEAN_SOURCES = [
    {
        "name": "BBC Europe News",
        "url": "https://feeds.bbci.co.uk/news/world/europe/rss.xml",
        "region": "Europe",
        "reliability": 9
    },
    {
        "name": "BBC World News",
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "region": "Global",
        "reliability": 9
    },
    {
        "name": "France 24 Europe",
        "url": "https://www.france24.com/en/europe/rss",
        "region": "Europe",
        "reliability": 8
    },
    {
        "name": "France 24 World",
        "url": "https://www.france24.com/en/rss",
        "region": "Global",
        "reliability": 8
    },
    {
        "name": "Al Jazeera Europe",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "region": "Global",
        "reliability": 8
    },
    {
        "name": "Reuters World",
        "url": "https://www.reutersagency.com/feed/?best-topics=political-general&post_type=best",
        "region": "Global",
        "reliability": 9
    },
]

# Keywords for missionary and security relevance
MISSIONARY_KEYWORDS = [
    'christian', 'church', 'religious', 'faith', 'missionary', 'persecution',
    'worship', 'gospel', 'ministry', 'evangelism', 'prayer', 'bible'
]

SECURITY_KEYWORDS = [
    'attack', 'violence', 'terror', 'threat', 'security', 'crisis', 'emergency',
    'protest', 'unrest', 'conflict', 'war', 'refugee', 'migration', 'border',
    'police', 'military', 'shooting', 'bomb', 'explosion', 'kidnap'
]

HEALTH_KEYWORDS = [
    'disease', 'outbreak', 'pandemic', 'epidemic', 'health', 'hospital',
    'emergency', 'vaccine', 'virus', 'infection', 'quarantine'
]

class EuropeanIntelligenceCollector:
    """Collects real intelligence from European news sources"""

    def __init__(self, db_path: str = 'data/intelligence.db'):
        """Initialize collector"""
        self.db_path = db_path
        self.conn = None
        self._ensure_database()

    def _ensure_database(self):
        """Ensure database and tables exist"""
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        # Database should already be initialized by quick_init_db.py

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def calculate_threat_level(self, title: str, content: str) -> float:
        """Calculate threat level based on content"""
        text = (title + ' ' + content).lower()

        security_score = sum(1 for kw in SECURITY_KEYWORDS if kw in text)
        health_score = sum(1 for kw in HEALTH_KEYWORDS if kw in text) * 0.8

        # Base threat calculation
        total_score = security_score * 1.5 + health_score

        # Normalize to 0-10 scale
        if total_score >= 8:
            return min(10.0, 7.0 + (total_score - 8) * 0.5)
        elif total_score >= 5:
            return 5.0 + (total_score - 5) * 0.67
        elif total_score >= 2:
            return 3.0 + (total_score - 2) * 0.67
        else:
            return 1.0 + total_score * 0.5

    def calculate_missionary_relevance(self, title: str, content: str) -> float:
        """Calculate missionary relevance based on content"""
        text = (title + ' ' + content).lower()

        missionary_score = sum(1 for kw in MISSIONARY_KEYWORDS if kw in text) * 2.0
        security_score = sum(1 for kw in SECURITY_KEYWORDS if kw in text) * 0.5
        health_score = sum(1 for kw in HEALTH_KEYWORDS if kw in text) * 0.3

        total_score = missionary_score + security_score + health_score

        # Normalize to 0-10 scale
        return min(10.0, 1.0 + total_score * 0.8)

    def extract_country(self, title: str, content: str) -> str:
        """Extract country name from content"""
        text = title + ' ' + content

        european_countries = [
            'France', 'Germany', 'Italy', 'Spain', 'Poland', 'Ukraine', 'Romania',
            'Netherlands', 'Belgium', 'Greece', 'Portugal', 'Sweden', 'Hungary',
            'Austria', 'Serbia', 'Switzerland', 'Bulgaria', 'Denmark', 'Finland',
            'Slovakia', 'Norway', 'Ireland', 'Croatia', 'Bosnia', 'Albania',
            'Lithuania', 'Slovenia', 'Latvia', 'Estonia', 'Moldova', 'Macedonia',
            'UK', 'United Kingdom', 'Britain', 'England', 'Scotland', 'Wales',
            'Czech Republic', 'Russia', 'Belarus', 'Turkey'
        ]

        for country in european_countries:
            if re.search(r'\b' + country + r'\b', text, re.IGNORECASE):
                return country

        return 'Europe'

    def extract_location(self, title: str, content: str, country: str) -> str:
        """Extract more specific location from content"""
        text = title + ' ' + content

        # Extract city names (simplified pattern)
        city_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+(' + country + r')'
        match = re.search(city_pattern, text)

        if match:
            return match.group(1)

        return country

    def extract_keywords(self, title: str, content: str) -> str:
        """Extract relevant keywords from content"""
        text = (title + ' ' + content).lower()
        keywords = []

        all_keywords = MISSIONARY_KEYWORDS + SECURITY_KEYWORDS + HEALTH_KEYWORDS
        for kw in all_keywords:
            if kw in text:
                keywords.append(kw)

        return ', '.join(keywords[:10]) if keywords else 'news, europe'

    def parse_rss(self, url: str) -> List[Dict]:
        """Parse RSS feed without feedparser"""
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Watchkeeper Intelligence Bot)'}
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)
            items = []

            # Try RSS 2.0 format first
            for item in root.findall('.//item')[:10]:
                title = item.find('title')
                description = item.find('description')
                link = item.find('link')
                pubDate = item.find('pubDate')

                items.append({
                    'title': title.text if title is not None else 'Untitled',
                    'description': description.text if description is not None else '',
                    'link': link.text if link is not None else url,
                    'pubDate': pubDate.text if pubDate is not None else None
                })

            # Try Atom format if no RSS items found
            if not items:
                for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry')[:10]:
                    title = entry.find('{http://www.w3.org/2005/Atom}title')
                    summary = entry.find('{http://www.w3.org/2005/Atom}summary')
                    link = entry.find('{http://www.w3.org/2005/Atom}link')
                    updated = entry.find('{http://www.w3.org/2005/Atom}updated')

                    items.append({
                        'title': title.text if title is not None else 'Untitled',
                        'description': summary.text if summary is not None else '',
                        'link': link.get('href') if link is not None else url,
                        'pubDate': updated.text if updated is not None else None
                    })

            return items
        except Exception as e:
            print(f"  Error parsing RSS: {e}")
            return []

    def collect_from_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect intelligence from a single source"""
        print(f"Collecting from {source['name']}...")

        try:
            entries = self.parse_rss(source['url'])

            if not entries:
                print(f"  ⚠ No entries found in {source['name']}")
                return []

            items = []
            for entry in entries:
                title = entry.get('title', 'Untitled')
                content = entry.get('description', '')

                # Clean HTML tags
                content = re.sub(r'<[^>]+>', '', content)

                # Calculate metrics
                threat = self.calculate_threat_level(title, content)
                relevance = self.calculate_missionary_relevance(title, content)

                # Only include items with some relevance (>2.0)
                if relevance < 2.0 and threat < 3.0:
                    continue

                # Extract location info
                country = self.extract_country(title, content)
                location = self.extract_location(title, content, country)
                keywords = self.extract_keywords(title, content)

                # Get publication date
                pub_date = datetime.now().isoformat() + 'Z'
                if entry.get('pubDate'):
                    pub_date = entry['pubDate']

                item = {
                    'title': title,
                    'content': content[:500],  # Limit content length
                    'summary': content[:200],
                    'source': source['name'],
                    'source_id': 1,  # Would be proper source ID in production
                    'raw_content': content,
                    'url': entry.get('link', source['url']),
                    'collection_date': datetime.now().isoformat() + 'Z',
                    'publication_date': pub_date,
                    'threat_level': threat,
                    'missionary_relevance': relevance,
                    'region': 'Europe',
                    'country': country,
                    'location': location,
                    'latitude': None,  # Would use geocoding in production
                    'longitude': None,
                    'keywords': keywords,
                    'sentiment': -0.3 if threat > 5.0 else 0.0,  # Simplified
                    'confidence': 0.7 + (source['reliability'] / 10) * 0.3
                }

                items.append(item)

            print(f"  ✓ Collected {len(items)} relevant items from {source['name']}")
            return items

        except Exception as e:
            print(f"  ❌ Error collecting from {source['name']}: {e}")
            return []

    def save_items(self, items: List[Dict[str, Any]]):
        """Save collected items to database"""
        if not items:
            print("No items to save")
            return 0

        cursor = self.conn.cursor()
        saved = 0

        for item in items:
            try:
                cursor.execute('''
                    INSERT INTO intelligence_items (
                        title, content, summary, source, source_id, raw_content, url,
                        collection_date, publication_date, threat_level, missionary_relevance,
                        region, country, location, latitude, longitude, keywords, sentiment,
                        confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item['title'], item['content'], item['summary'], item['source'],
                    item['source_id'], item['raw_content'], item['url'],
                    item['collection_date'], item['publication_date'],
                    item['threat_level'], item['missionary_relevance'],
                    item['region'], item['country'], item['location'],
                    item['latitude'], item['longitude'], item['keywords'],
                    item['sentiment'], item['confidence']
                ))
                saved += 1
            except sqlite3.IntegrityError:
                # Skip duplicates
                continue
            except Exception as e:
                print(f"Error saving item: {e}")
                continue

        self.conn.commit()
        return saved

    def collect_all(self) -> int:
        """Collect from all European sources"""
        print("=" * 80)
        print("EUROPEAN INTELLIGENCE COLLECTION")
        print("=" * 80)
        print(f"Sources: {len(EUROPEAN_SOURCES)}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 80)
        print()

        all_items = []

        for source in EUROPEAN_SOURCES:
            items = self.collect_from_source(source)
            all_items.extend(items)
            time.sleep(1)  # Rate limiting

        print()
        print(f"Total items collected: {len(all_items)}")

        # Save to database
        saved = self.save_items(all_items)
        print(f"Items saved to database: {saved}")

        # Show statistics
        if all_items:
            avg_threat = sum(item['threat_level'] for item in all_items) / len(all_items)
            avg_relevance = sum(item['missionary_relevance'] for item in all_items) / len(all_items)
            high_threat = sum(1 for item in all_items if item['threat_level'] >= 6.0)

            print()
            print("COLLECTION STATISTICS:")
            print(f"  Average Threat Level: {avg_threat:.1f}/10")
            print(f"  Average Relevance: {avg_relevance:.1f}/10")
            print(f"  High Threat Items (≥6.0): {high_threat}")

        return saved

def main():
    """Main entry point"""
    collector = EuropeanIntelligenceCollector()

    try:
        # Clear old sample data
        cursor = collector.conn.cursor()
        cursor.execute("DELETE FROM intelligence_items")
        collector.conn.commit()
        print("✓ Cleared old sample data\n")

        # Collect real European intelligence
        saved = collector.collect_all()

        if saved > 0:
            print()
            print("=" * 80)
            print("✓ COLLECTION COMPLETE")
            print(f"✓ Database: data/intelligence.db")
            print(f"✓ Total items: {saved}")
            print("=" * 80)
        else:
            print()
            print("⚠ No items were collected. Check network connection and source URLs.")

    finally:
        collector.close()

if __name__ == '__main__':
    main()
