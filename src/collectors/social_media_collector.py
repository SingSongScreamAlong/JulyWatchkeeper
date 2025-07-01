"""
Social Media Collector for WATCHKEEPER

This module implements a collector for social media sources.
"""

import asyncio
import aiohttp
import json
import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.collectors.base_collector import BaseCollector
from src.utils.logger import get_logger
from src.utils.config import get_config

class SocialMediaCollector(BaseCollector):
    """
    Collector for social media sources
    
    This collector fetches posts from various social media platforms and extracts
    relevant information for intelligence analysis.
    """
    
    # Social media platform configurations
    PLATFORM_CONFIGS = {
        "twitter": {
            "api_url": "https://api.twitter.com/2/tweets/search/recent",
            "reliability_score": 0.6,
            "rate_limit": 450,  # Requests per 15-minute window
            "auth_required": True
        },
        "reddit": {
            "api_url": "https://www.reddit.com/r/{subreddit}/new.json",
            "reliability_score": 0.5,
            "rate_limit": 60,  # Requests per minute
            "auth_required": False
        },
        "mastodon": {
            "api_url": "https://{instance}/api/v1/timelines/public",
            "reliability_score": 0.4,
            "rate_limit": 300,  # Requests per 5-minute window
            "auth_required": False
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
    
    def __init__(self, platform: str, config: Dict[str, Any] = None):
        """
        Initialize the social media collector
        
        Args:
            platform: Social media platform name (twitter, reddit, mastodon)
            config: Additional configuration parameters
        """
        if platform not in self.PLATFORM_CONFIGS:
            raise ValueError(f"Unsupported social media platform: {platform}")
        
        self.platform = platform
        self.platform_config = self.PLATFORM_CONFIGS[platform]
        rate_limit = self.platform_config.get("rate_limit", 60)
        
        super().__init__(f"social_media.{platform}", rate_limit)
        
        self.reliability_score = self.platform_config.get("reliability_score", 0.5)
        self.config = config or {}
        self.auth_headers = {}
        self.last_id = None  # For pagination/tracking
        self.logger = get_logger(f"watchkeeper.collectors.social_media.{platform}")
        
        # Load API keys and tokens from config
        self._load_auth_credentials()
    
    def _load_auth_credentials(self):
        """Load authentication credentials from configuration"""
        if not self.platform_config.get("auth_required", False):
            return
        
        # Get config
        config = get_config()
        
        # Set up authentication headers based on platform
        if self.platform == "twitter":
            bearer_token = config.get("social_media", {}).get("twitter", {}).get("bearer_token")
            if bearer_token:
                self.auth_headers = {"Authorization": f"Bearer {bearer_token}"}
            else:
                self.logger.warning("Twitter API bearer token not found in configuration")
        
        elif self.platform == "reddit":
            client_id = config.get("social_media", {}).get("reddit", {}).get("client_id")
            client_secret = config.get("social_media", {}).get("reddit", {}).get("client_secret")
            if client_id and client_secret:
                self.auth_headers = {
                    "User-Agent": "WATCHKEEPER/1.0 (Intelligence Platform)",
                    "Authorization": f"Basic {client_id}:{client_secret}"
                }
        
        elif self.platform == "mastodon":
            access_token = config.get("social_media", {}).get("mastodon", {}).get("access_token")
            if access_token:
                self.auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect posts from the social media platform
        
        Returns:
            List[Dict[str, Any]]: List of collected posts
        """
        collected_posts = []
        
        try:
            # Determine search parameters based on platform
            params = self._get_search_params()
            
            # Get API URL
            api_url = self._get_api_url()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    api_url, 
                    headers=self.auth_headers,
                    params=params,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to fetch from {self.platform}: {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    # Parse response based on platform
                    posts = self._extract_posts(data)
                    
                    for post in posts:
                        # Parse the post
                        post_data = self.parse_content(post)
                        if post_data:
                            # Assess relevance
                            relevance = self.assess_relevance(post_data)
                            post_data["relevance_score"] = relevance
                            
                            # Only include posts with sufficient relevance
                            if relevance >= 0.3:
                                collected_posts.append(post_data)
                                
                                # Update last_id for pagination if applicable
                                if "id" in post:
                                    self.last_id = post["id"]
        
        except Exception as e:
            self.logger.error(f"Error collecting from {self.platform}: {e}", exc_info=True)
        
        return collected_posts
    
    def _get_search_params(self) -> Dict[str, Any]:
        """
        Get search parameters based on platform
        
        Returns:
            Dict[str, Any]: Search parameters
        """
        params = {}
        
        if self.platform == "twitter":
            # Twitter API v2 search parameters
            query = " OR ".join([f"\"{keyword}\"" for keyword in self.RELEVANCE_KEYWORDS[:10]])
            params = {
                "query": query,
                "max_results": 10,
                "tweet.fields": "created_at,author_id,geo,lang",
                "expansions": "geo.place_id"
            }
            
            # Add pagination if we have a last_id
            if self.last_id:
                params["since_id"] = self.last_id
        
        elif self.platform == "reddit":
            # Reddit API parameters
            params = {
                "limit": 25
            }
            
            # Add pagination if we have a last_id
            if self.last_id:
                params["after"] = self.last_id
        
        elif self.platform == "mastodon":
            # Mastodon API parameters
            params = {
                "limit": 20
            }
            
            # Add pagination if we have a last_id
            if self.last_id:
                params["since_id"] = self.last_id
        
        return params
    
    def _get_api_url(self) -> str:
        """
        Get the API URL for the platform
        
        Returns:
            str: API URL
        """
        api_url = self.platform_config["api_url"]
        
        # Replace placeholders in URL
        if self.platform == "reddit":
            subreddit = self.config.get("subreddit", "europe")
            api_url = api_url.replace("{subreddit}", subreddit)
        
        elif self.platform == "mastodon":
            instance = self.config.get("instance", "mastodon.social")
            api_url = api_url.replace("{instance}", instance)
        
        return api_url
    
    def _extract_posts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract posts from API response
        
        Args:
            data: API response data
            
        Returns:
            List[Dict[str, Any]]: List of posts
        """
        posts = []
        
        if self.platform == "twitter":
            # Twitter API v2 response format
            if "data" in data and isinstance(data["data"], list):
                posts = data["data"]
        
        elif self.platform == "reddit":
            # Reddit API response format
            if "data" in data and "children" in data["data"]:
                posts = [post["data"] for post in data["data"]["children"]]
        
        elif self.platform == "mastodon":
            # Mastodon API response format (already a list)
            if isinstance(data, list):
                posts = data
        
        return posts
    
    def parse_content(self, content: Any) -> Dict[str, Any]:
        """
        Parse content from the platform into a standardized format
        
        Args:
            content: Raw content from the platform
            
        Returns:
            Dict[str, Any]: Parsed post data
        """
        if not content:
            return {}
        
        try:
            if self.platform == "twitter":
                return self._parse_twitter(content)
            elif self.platform == "reddit":
                return self._parse_reddit(content)
            elif self.platform == "mastodon":
                return self._parse_mastodon(content)
            else:
                return {}
        
        except Exception as e:
            self.logger.error(f"Error parsing {self.platform} content: {e}", exc_info=True)
            return {}
    
    def _parse_twitter(self, tweet: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Twitter tweet data"""
        return {
            "id": tweet.get("id", ""),
            "content": tweet.get("text", ""),
            "author": tweet.get("author_id", ""),
            "created_at": tweet.get("created_at", datetime.now().isoformat()),
            "language": tweet.get("lang", "en"),
            "locations": self._extract_locations_from_text(tweet.get("text", "")),
            "platform": "twitter",
            "url": f"https://twitter.com/i/web/status/{tweet.get('id', '')}"
        }
    
    def _parse_reddit(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Reddit post data"""
        content = post.get("selftext", "") or post.get("title", "")
        
        return {
            "id": post.get("name", ""),
            "title": post.get("title", ""),
            "content": content,
            "author": post.get("author", ""),
            "created_at": datetime.fromtimestamp(post.get("created_utc", time.time())).isoformat(),
            "subreddit": post.get("subreddit", ""),
            "locations": self._extract_locations_from_text(content),
            "platform": "reddit",
            "url": f"https://www.reddit.com{post.get('permalink', '')}"
        }
    
    def _parse_mastodon(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Mastodon post data"""
        content = post.get("content", "")
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        return {
            "id": post.get("id", ""),
            "content": content,
            "author": post.get("account", {}).get("username", ""),
            "created_at": post.get("created_at", datetime.now().isoformat()),
            "language": post.get("language", "en"),
            "locations": self._extract_locations_from_text(content),
            "platform": "mastodon",
            "url": post.get("url", "")
        }
    
    def assess_relevance(self, content: Dict[str, Any]) -> float:
        """
        Assess the relevance of a post to missionary operations
        
        Args:
            content: Parsed post content
            
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
            keyword_density = keyword_matches / min(text_length, 50)  # Cap at 50 words to normalize
            relevance_score = min(keyword_density * 5.0, 1.0)  # Scale and cap at 1.0
        else:
            relevance_score = 0.0
        
        # Boost score for posts with certain high-priority keywords
        high_priority_keywords = ["emergency", "evacuation", "attack", "threat", "crisis", "alert"]
        if any(keyword in text for keyword in high_priority_keywords):
            relevance_score = min(relevance_score + 0.3, 1.0)
        
        # Apply platform-specific reliability adjustment
        relevance_score *= self.reliability_score
        
        return relevance_score
    
    def _extract_locations_from_text(self, text: str) -> List[str]:
        """
        Extract location mentions from text
        
        Args:
            text: Post text
            
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
