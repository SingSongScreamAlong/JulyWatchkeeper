"""
Government Alerts Collector for WATCHKEEPER

This module implements a collector for government alerts and travel advisories.
"""

import asyncio
import aiohttp
import json
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from src.collectors.base_collector import BaseCollector
from src.utils.logger import get_logger
from src.utils.config import get_config

class GovernmentCollector(BaseCollector):
    """
    Collector for government alerts and travel advisories
    
    This collector fetches alerts from various government sources and extracts
    relevant information for intelligence analysis.
    """
    
    # Government source configurations
    SOURCE_CONFIGS = {
        "uk_fco": {
            "url": "https://www.gov.uk/foreign-travel-advice",
            "country_selector": ".gem-c-document-list__item-title",
            "alert_selector": ".gem-c-govspeak",
            "reliability_score": 0.9,
            "rate_limit": 30  # Requests per minute
        },
        "us_state": {
            "url": "https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html",
            "country_selector": ".tsg-rwd-qf-box-container a",
            "alert_selector": ".tsg-rwd-emergency-alert",
            "reliability_score": 0.9,
            "rate_limit": 30  # Requests per minute
        },
        "eu_echo": {
            "url": "https://civil-protection-humanitarian-aid.ec.europa.eu/what/civil-protection/emergency-response-coordination-centre-ercc_en",
            "alert_selector": ".ecl-content-item",
            "reliability_score": 0.85,
            "rate_limit": 30  # Requests per minute
        }
    }
    
    # Countries of interest for missionary operations
    COUNTRIES_OF_INTEREST = [
        "France", "Germany", "United Kingdom", "Italy", "Spain", 
        "Netherlands", "Belgium", "Sweden", "Norway", "Denmark", 
        "Finland", "Poland", "Austria", "Switzerland", "Greece", 
        "Portugal", "Ireland", "Czech Republic", "Hungary", "Romania",
        "Bulgaria", "Croatia", "Serbia", "Ukraine", "Turkey"
    ]
    
    def __init__(self, source: str, rate_limit: Optional[int] = None):
        """
        Initialize the government collector
        
        Args:
            source: Government source name (uk_fco, us_state, eu_echo)
            rate_limit: Override default rate limit if provided
        """
        if source not in self.SOURCE_CONFIGS:
            raise ValueError(f"Unsupported government source: {source}")
        
        self.source_name = source
        self.config = self.SOURCE_CONFIGS[source]
        
        # Use provided rate limit or default from source config
        source_rate_limit = rate_limit or self.config.get("rate_limit", 30)
        
        super().__init__(f"government.{source}", source_rate_limit)
        
        self.reliability_score = self.config.get("reliability_score", 0.8)
        self.last_alerts = {}  # To track already processed alerts by country
        self.logger = get_logger(f"watchkeeper.collectors.government.{source}")
    
    async def collect(self) -> List[Dict[str, Any]]:
        """
        Collect alerts from the government source
        
        Returns:
            List[Dict[str, Any]]: List of collected alerts
        """
        collected_alerts = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Fetch the main page
                async with session.get(self.config["url"], timeout=30) as response:
                    if response.status != 200:
                        self.logger.error(f"Failed to fetch {self.config['url']}: {response.status}")
                        return []
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    if self.source_name in ["uk_fco", "us_state"]:
                        # These sources list countries, so we need to fetch individual country pages
                        country_links = soup.select(self.config["country_selector"])
                        
                        # Filter to countries of interest and limit to 5 for testing
                        filtered_links = []
                        for link in country_links:
                            country_name = link.get_text().strip()
                            if any(country.lower() in country_name.lower() for country in self.COUNTRIES_OF_INTEREST):
                                filtered_links.append(link)
                        
                        # Process each country (limited to 5 for testing)
                        for i, link in enumerate(filtered_links[:5]):
                            # Apply rate limiting between requests
                            if i > 0:
                                await asyncio.sleep(2)
                            
                            country_name = link.get_text().strip()
                            href = link.get('href')
                            
                            # Make sure URL is absolute
                            if not href.startswith('http'):
                                if href.startswith('/'):
                                    base_url = '/'.join(self.config["url"].split('/')[:3])
                                    href = f"{base_url}{href}"
                                else:
                                    base_url = '/'.join(self.config["url"].split('/')[:-1])
                                    href = f"{base_url}/{href}"
                            
                            # Skip if we've already processed this country recently
                            if country_name in self.last_alerts:
                                last_check = self.last_alerts[country_name]["last_check"]
                                # Only check once per day
                                if (datetime.now() - last_check).total_seconds() < 86400:  # 24 hours
                                    continue
                            
                            try:
                                # Fetch the country page
                                async with session.get(href, timeout=30) as country_response:
                                    if country_response.status != 200:
                                        continue
                                    
                                    country_html = await country_response.text()
                                    country_soup = BeautifulSoup(country_html, 'html.parser')
                                    
                                    # Parse the country page
                                    alert_data = self._parse_country_page(country_soup, country_name, href)
                                    
                                    if alert_data:
                                        # Check if alert has changed
                                        if country_name in self.last_alerts:
                                            last_content = self.last_alerts[country_name]["content"]
                                            if last_content == alert_data["content"]:
                                                # Update last check time but don't add to collected alerts
                                                self.last_alerts[country_name]["last_check"] = datetime.now()
                                                continue
                                        
                                        # Add to collected alerts
                                        collected_alerts.append(alert_data)
                                        
                                        # Update last alerts
                                        self.last_alerts[country_name] = {
                                            "content": alert_data["content"],
                                            "last_check": datetime.now()
                                        }
                            
                            except Exception as e:
                                self.logger.error(f"Error processing {country_name} page: {e}")
                                continue
                    
                    elif self.source_name == "eu_echo":
                        # EU ECHO has alerts directly on the main page
                        alerts = soup.select(self.config["alert_selector"])
                        
                        for alert in alerts:
                            alert_data = self._parse_eu_echo_alert(alert)
                            if alert_data:
                                collected_alerts.append(alert_data)
        
        except Exception as e:
            self.logger.error(f"Error collecting from {self.source_name}: {e}", exc_info=True)
        
        return collected_alerts
    
    def _parse_country_page(self, soup: BeautifulSoup, country: str, url: str) -> Dict[str, Any]:
        """
        Parse a country page for alerts
        
        Args:
            soup: BeautifulSoup object of the country page
            country: Country name
            url: URL of the country page
            
        Returns:
            Dict[str, Any]: Parsed alert data
        """
        try:
            # Extract alert content
            alert_element = soup.select_one(self.config["alert_selector"])
            
            if not alert_element:
                return None
            
            alert_content = alert_element.get_text().strip()
            
            # Extract summary
            summary = ""
            summary_element = soup.select_one("meta[name='description']")
            if summary_element:
                summary = summary_element.get('content', '')
            
            # Extract publication date
            date = None
            date_element = soup.select_one("time")
            if date_element:
                date = date_element.get('datetime') or date_element.get_text()
            
            if not date:
                # Try other common date formats
                date_patterns = [
                    soup.select_one('.date'),
                    soup.select_one('.published-date'),
                    soup.select_one('[datetime]')
                ]
                
                for pattern in date_patterns:
                    if pattern:
                        date = pattern.get('datetime') or pattern.get_text()
                        break
            
            # If still no date, use current time
            if not date:
                date = datetime.now().isoformat()
            
            # Extract alert level if available
            alert_level = None
            if self.source_name == "us_state":
                level_element = soup.select_one(".tsg-rwd-alert-level")
                if level_element:
                    alert_level = level_element.get_text().strip()
            
            # Extract locations
            locations = [country]
            
            return {
                "country": country,
                "title": f"{self.source_name.upper()} Travel Advisory for {country}",
                "content": alert_content,
                "summary": summary,
                "publication_date": date,
                "source_name": f"government.{self.source_name}",
                "alert_level": alert_level,
                "language": "en",  # Assuming English
                "locations": locations,
                "url": url,
                "collection_time": datetime.now().isoformat(),
                "alert_type": "travel_advisory"
            }
        
        except Exception as e:
            self.logger.error(f"Error parsing country page: {e}", exc_info=True)
            return None
    
    def _parse_eu_echo_alert(self, alert_element: Any) -> Dict[str, Any]:
        """
        Parse an EU ECHO alert
        
        Args:
            alert_element: Alert element from BeautifulSoup
            
        Returns:
            Dict[str, Any]: Parsed alert data
        """
        try:
            # Extract title
            title_element = alert_element.select_one("h3")
            title = title_element.get_text().strip() if title_element else ""
            
            # Extract content
            content_element = alert_element.select_one("p")
            content = content_element.get_text().strip() if content_element else ""
            
            # Extract link
            link = ""
            link_element = alert_element.select_one("a")
            if link_element:
                href = link_element.get('href')
                if href:
                    if not href.startswith('http'):
                        base_url = "https://civil-protection-humanitarian-aid.ec.europa.eu"
                        link = f"{base_url}{href}"
                    else:
                        link = href
            
            # Extract date
            date = None
            date_element = alert_element.select_one("time") or alert_element.select_one(".date")
            if date_element:
                date = date_element.get('datetime') or date_element.get_text()
            
            if not date:
                date = datetime.now().isoformat()
            
            # Extract locations from title and content
            locations = []
            for country in self.COUNTRIES_OF_INTEREST:
                if country in title or country in content:
                    locations.append(country)
            
            # If no specific countries found, mark as "Europe"
            if not locations:
                locations = ["Europe"]
            
            return {
                "title": title,
                "content": content,
                "summary": content[:200] + "..." if len(content) > 200 else content,
                "publication_date": date,
                "source_name": "government.eu_echo",
                "language": "en",  # Assuming English
                "locations": locations,
                "url": link,
                "collection_time": datetime.now().isoformat(),
                "alert_type": "emergency_alert"
            }
        
        except Exception as e:
            self.logger.error(f"Error parsing EU ECHO alert: {e}", exc_info=True)
            return None
    
    def parse_content(self, content: Any) -> Dict[str, Any]:
        """
        Parse content from the source into a standardized format
        
        Args:
            content: Raw content from the source
            
        Returns:
            Dict[str, Any]: Parsed alert data
        """
        # This method is required by the BaseCollector interface
        # For government collectors, parsing is done in _parse_country_page and _parse_eu_echo_alert
        return content
    
    def assess_relevance(self, content: Dict[str, Any]) -> float:
        """
        Assess the relevance of an alert to missionary operations
        
        Args:
            content: Parsed alert content
            
        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        if not content or not content.get("content"):
            return 0.0
        
        # Convert content to lowercase for case-insensitive matching
        text = (content.get("title", "") + " " + content.get("content", "")).lower()
        
        # High-priority keywords for government alerts
        high_priority_keywords = [
            "evacuation", "emergency", "warning", "alert", "threat", "attack",
            "terrorism", "security", "danger", "avoid travel", "do not travel",
            "high risk", "imminent", "lockdown", "civil unrest", "violent"
        ]
        
        # Medium-priority keywords
        medium_priority_keywords = [
            "caution", "monitor", "aware", "vigilant", "exercise caution",
            "protest", "demonstration", "disruption", "delay", "restriction"
        ]
        
        # Count keyword matches
        high_matches = sum(1 for keyword in high_priority_keywords if keyword in text)
        medium_matches = sum(1 for keyword in medium_priority_keywords if keyword in text)
        
        # Calculate base relevance score
        relevance_score = min((high_matches * 0.2) + (medium_matches * 0.1), 0.9)
        
        # Boost score for alerts with specific alert levels
        if content.get("alert_level"):
            alert_level = content["alert_level"].lower()
            if "level 4" in alert_level or "do not travel" in alert_level:
                relevance_score = min(relevance_score + 0.3, 1.0)
            elif "level 3" in alert_level or "reconsider travel" in alert_level:
                relevance_score = min(relevance_score + 0.2, 1.0)
        
        # Apply source reliability adjustment
        relevance_score *= self.reliability_score
        
        return relevance_score
