"""
News Collector for WATCHKEEPER

This module implements a collector for news sources.
"""

import asyncio
import aiohttp
import re
import time
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from src.collectors.base_collector import BaseCollector
from src.utils.logger import get_logger

class NewsCollector(BaseCollector):
    """
    Collector for news sources
    
    This collector fetches articles from various news sources and extracts
    relevant information for intelligence analysis.
    """
    
    # News source configurations
    SOURCE_CONFIGS = {
        "bbc": {
            "url": "https://www.bbc.com/news/world/europe",
            "article_selector": "a.gs-c-promo-heading",
            "title_selector": ".gs-c-promo-heading__title",
            "content_selector": "article",
            "reliability_score": 0.85
        },
        "reuters": {
            "url": "https://www.reuters.com/world/europe/",
            "article_selector": "a.media-story-card__heading__eqhp9",
            "title_selector": ".media-story-card__heading__eqhp9 span",
            "content_selector": ".article-body__content__17Yit",
            "reliability_score": 0.9
        },
        "dw": {
            "url": "https://www.dw.com/en/top-stories/europe/s-1433",
            "article_selector": "a.teaser__link",
            "title_selector": ".teaser__title",
            "content_selector": ".longText",
            "reliability_score": 0.8
        }
    }
    
    # Keywords relevant to missionary operations
    RELEVANCE_KEYWORDS = [
        # Security-related
        "protest", "riot", "demonstration", "unrest", "attack", "terrorism", "security",
        "emergency", "evacuation", "lockdown", "threat", "warning", "alert", "crisis",
        
        # Travel-related
        "airport", "flight", "cancel", "delay", "border", "restriction", "transport",
        "strike", "disruption", "closure", "visa", "passport", "immigration",
        
        # Political
        "election", "government", "policy", "law", "regulation", "ban", "minister",
        "president", "parliament", "legislation", "political", "diplomatic",
        
        # Religious
        "church", "christian", "missionary", "religion", "worship", "faith", "prayer",
        "persecution", "freedom", "belief", "evangelical", "ministry",
        
        # Health
        "outbreak", "epidemic", "pandemic", "disease", "virus", "infection", "health",
        "hospital", "medical", "emergency", "quarantine", "vaccination",
        
        # Natural disasters
        "earthquake", "flood", "fire", "storm", "hurricane", "tsunami", "disaster",
        "evacuation", "emergency", "rescue", "relief", "aid"
    ]
    
    def __init__(self, source: str, rate_limit: int = 60, languages: List[str] = None):
        """
        Initialize the news collector
        
        Args:
            source: News source name (bbc, reuters, dw)
            rate_limit: Maximum number of requests per minute
            languages: List of languages to collect (ISO 639-1 codes)
        """
        super().__init__(source, rate_limit)
        
        if source not in self.SOURCE_CONFIGS:
            raise ValueError(f"Unsupported news source: {source}")
        
        self.config = self.SOURCE_CONFIGS[source]
        self.reliability_score = self.config.get("reliability_score", 0.7)
        self.languages = languages or ["en"]
        self.last_articles = set()  # To track already processed articles
        self.logger = get_logger(f"watchkeeper.collectors.news.{source}")
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect news articles from the source
        
        Returns:
            List[Dict[str, Any]]: List of collected news articles
        """
        collected_articles = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch the main page
                async with session.get(self.config["url"], timeout=30) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to fetch {self.config['url']}: {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Find all article links
                    article_links = soup.select(self.config["article_selector"])
                    self.logger.debug(f"Found {len(article_links)} article links on {self.config['url']}")
                    
                    # Process each article (limited to 5 for testing)
                    for i, link in enumerate(article_links[:5]):
                        # Extract article URL
                        href = link.get('href')
                        if not href:
                            continue
                        
                        # Make sure URL is absolute
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                base_url = '/'.join(self.config["url"].split('/')[:3])
                                href = f"{base_url}{href}"
                            else:
                                base_url = '/'.join(self.config["url"].split('/')[:-1])
                                href = f"{base_url}/{href}"
                        
                        # Skip if already processed
                        if href in self.last_articles:
                            continue
                        
                        # Apply rate limiting between article requests
                        if i > 0:
                            await asyncio.sleep(5)  # 5 seconds between article requests
                        
                        try:
                            # Fetch the article
                            async with session.get(href, timeout=30) as article_response:
                                if article_response.status != 200:
                                    continue
                                
                                article_html = await article_response.text()
                                article_soup = BeautifulSoup(article_html, 'html.parser')
                                
                                # Parse the article
                                article_data = self.parse_content(article_soup)
                                if article_data:
                                    article_data["url"] = href
                                    
                                    # Assess relevance
                                    relevance = self.assess_relevance(article_data)
                                    article_data["relevance_score"] = relevance
                                    
                                    # Only include articles with sufficient relevance
                                    if relevance >= 0.3:
                                        collected_articles.append(article_data)
                                        self.last_articles.add(href)
                        
                        except Exception as e:
                            self.logger.error(f"Error processing article {href}: {e}")
                            continue
        
        except Exception as e:
            self.logger.error(f"Error collecting from {self.source}: {e}", exc_info=True)
        
        # Keep the last_articles set from growing too large
        if len(self.last_articles) > 100:
            self.last_articles = set(list(self.last_articles)[-100:])
        
        return collected_articles
    
    def parse_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Parse article content from BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object of the article page
            
        Returns:
            Dict[str, Any]: Parsed article data
        """
        try:
            # Extract title
            title_element = soup.select_one(self.config["title_selector"])
            title = title_element.get_text().strip() if title_element else ""
            
            if not title:
                title = soup.title.get_text() if soup.title else ""
            
            # Extract content
            content_element = soup.select_one(self.config["content_selector"])
            content = content_element.get_text().strip() if content_element else ""
            
            if not content:
                # Fallback: get all paragraphs
                paragraphs = soup.select("p")
                content = "\n".join([p.get_text().strip() for p in paragraphs])
            
            # Extract publication date
            date = None
            date_meta = soup.select_one('meta[property="article:published_time"]')
            if date_meta:
                date = date_meta.get('content')
            
            if not date:
                # Try common date formats
                date_patterns = [
                    soup.select_one('time'),
                    soup.select_one('.date'),
                    soup.select_one('.article-date'),
                    soup.select_one('[datetime]')
                ]
                
                for pattern in date_patterns:
                    if pattern:
                        date = pattern.get('datetime') or pattern.get_text()
                        break
            
            # If still no date, use current time
            if not date:
                date = datetime.now().isoformat()
            
            # Extract location mentions
            locations = self._extract_locations(content)
            
            return {
                "title": title,
                "content": content,
                "publication_date": date,
                "source_name": self.source,
                "language": self._detect_language(content),
                "locations": locations,
                "collection_time": datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error parsing article content: {e}", exc_info=True)
            return {}
    
    def assess_relevance(self, content: Dict[str, Any]) -> float:
        """
        Assess the relevance of an article to missionary operations
        
        Args:
            content: Parsed article content
            
        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        if not content or not content.get("content"):
            return 0.0
        
        # Convert content to lowercase for case-insensitive matching
        text = (content.get("title", "") + " " + content.get("content", "")).lower()
        
        # Count keyword matches
        keyword_matches = sum(1 for keyword in self.RELEVANCE_KEYWORDS if keyword.lower() in text)
        
        # Calculate relevance score based on keyword density
        text_length = len(text.split())
        if text_length > 0:
            keyword_density = keyword_matches / min(text_length, 100)  # Cap at 100 words to normalize
            relevance_score = min(keyword_density * 5.0, 1.0)  # Scale and cap at 1.0
        else:
            relevance_score = 0.0
        
        # Boost score for articles with certain high-priority keywords
        high_priority_keywords = ["emergency", "evacuation", "attack", "threat", "crisis", "alert"]
        if any(keyword in text for keyword in high_priority_keywords):
            relevance_score = min(relevance_score + 0.3, 1.0)
        
        return relevance_score
    
    def _extract_locations(self, text: str) -> List[str]:
        """
        Extract location mentions from text
        
        Args:
            text: Article text
            
        Returns:
            List[str]: List of extracted locations
        """
        # This is a simplified implementation
        # In a real system, this would use NER (Named Entity Recognition)
        
        # List of European countries and major cities
        european_locations = [
            "France", "Paris", "Lyon", "Marseille",
            "Germany", "Berlin", "Munich", "Hamburg",
            "UK", "London", "Manchester", "Edinburgh",
            "Italy", "Rome", "Milan", "Venice",
            "Spain", "Madrid", "Barcelona", "Seville",
            "Netherlands", "Amsterdam", "Rotterdam",
            "Belgium", "Brussels", "Antwerp",
            "Sweden", "Stockholm", "Gothenburg",
            "Norway", "Oslo", "Bergen",
            "Denmark", "Copenhagen",
            "Finland", "Helsinki",
            "Poland", "Warsaw", "Krakow",
            "Austria", "Vienna", "Salzburg",
            "Switzerland", "Zurich", "Geneva",
            "Greece", "Athens", "Thessaloniki",
            "Portugal", "Lisbon", "Porto",
            "Ireland", "Dublin", "Cork",
            "Czech Republic", "Prague",
            "Hungary", "Budapest"
        ]
        
        found_locations = []
        for location in european_locations:
            if location in text:
                found_locations.append(location)
        
        return found_locations
    
    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the text
        
        Args:
            text: Text to detect language for
            
        Returns:
            str: ISO 639-1 language code
        """
        # This is a simplified implementation
        # In a real system, this would use a language detection library
        
        # For now, we'll just assume English
        return "en"
