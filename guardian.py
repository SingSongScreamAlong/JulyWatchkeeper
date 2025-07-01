#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""WATCHKEEPER - Autonomous Intelligence System for Missionary Protection

This module implements the core functionality of the WATCHKEEPER system, including
threat assessment, stealth web navigation, intelligence collection, and autonomous
investigation capabilities.
"""

import os
import sys
import json
import time
import logging
import asyncio
import signal
import random
import sqlite3
import traceback
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field

# Import Europe filter
from europe_filter import filter_intelligence, EuropeFilter

try:
    from playwright.async_api import async_playwright
    from bs4 import BeautifulSoup
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    import aiohttp
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    import feedparser
except ImportError:
    print("Required packages not found. Please install with: pip install playwright bs4 nltk aiohttp geopy feedparser")
    sys.exit(1)

# Configure logging
logging_dir = Path('data/logs')
logging_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(logging_dir / 'watchkeeper.log', mode='a')
    ]
)
logger = logging.getLogger('watchkeeper')

# Ensure NLTK data is available
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    logger.warning("NLTK Vader lexicon not found. Will be downloaded during setup.")


@dataclass
class IntelligenceItem:
    """Data structure for intelligence items"""
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    source: str = ""
    url: str = ""
    collection_date: str = field(default_factory=lambda: datetime.now().isoformat())
    publication_date: Optional[str] = None
    threat_level: float = 0.0
    missionary_relevance: float = 0.0
    region: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    keywords: List[str] = field(default_factory=list)
    sentiment: float = 0.0
    confidence: float = 0.0
    investigation_status: str = "pending"  # pending, in_progress, completed
    investigation_data: Dict[str, Any] = field(default_factory=dict)


class MissionaryThreatAssessment:
    """AI-powered threat assessment specifically for missionary contexts"""
    
    def __init__(self, db_path: str = 'data/intelligence.db'):
        # Initialize database path for source tracking
        self.db_path = db_path
        
        # Initialize threat assessment parameters
        self.threat_keywords = {
            'high': [
                'persecution', 'arrest', 'detained', 'violence', 'attack', 'killed',
                'hostage', 'kidnap', 'extremist', 'terrorist', 'banned', 'illegal',
                'deport', 'expel', 'surveillance', 'monitor', 'raid', 'torture',
                'missionary expulsion', 'visa denial', 'church closure', 'religious ban'
            ],
            'medium': [
                'restrict', 'limit', 'control', 'regulation', 'law', 'protest',
                'unrest', 'tension', 'conflict', 'warning', 'threat', 'risk',
                'opposition', 'hostile', 'suspicious', 'investigate', 'question',
                'missionary restriction', 'religious registration', 'visa difficulty'
            ],
            'low': [
                'policy', 'change', 'concern', 'attention', 'review', 'scrutiny',
                'report', 'observe', 'notice', 'track', 'follow', 'watch',
                'political', 'religious freedom', 'minority', 'group', 'community',
                'missionary', 'european missionary', 'european church', 'european aid'
            ]
        }
        
        # Missionary relevance keywords
        self.missionary_keywords = {
            'direct': [
                'missionary', 'christian', 'church', 'evangelist', 'religious worker',
                'ministry', 'convert', 'baptism', 'bible', 'gospel', 'witness',
                'faith-based', 'religious organization', 'mission trip', 'outreach',
                'european missionary', 'european church', 'european christian',
                'western missionary', 'foreign missionary', 'mission agency'
            ],
            'indirect': [
                'religious freedom', 'worship', 'belief', 'faith', 'prayer', 'religion',
                'spiritual', 'congregation', 'service', 'community', 'volunteer',
                'humanitarian', 'aid worker', 'charity', 'nonprofit', 'NGO',
                'religious affairs', 'religious policy', 'religious registration',
                'visa policy', 'foreign religious worker', 'religious visa'
            ],
            'opportunity': [
                'open', 'welcome', 'invite', 'allow', 'permit', 'support', 'encourage',
                'cooperation', 'partnership', 'assistance', 'development', 'education',
                'medical', 'healthcare', 'training', 'teaching', 'relief', 'humanitarian',
                'european aid', 'european assistance', 'european partnership',
                'european development', 'european funding', 'european cooperation'
            ],
            'persecution': [
                'persecution', 'restrict', 'ban', 'prohibit', 'prevent', 'deny',
                'reject', 'oppose', 'hostile', 'threat', 'danger', 'risk', 'unsafe',
                'unwelcome', 'illegal', 'criminal', 'punish', 'detain', 'arrest',
                'visa denial', 'visa restriction', 'expulsion', 'deportation',
                'foreign agent', 'foreign influence', 'foreign organization',
                'religious extremism', 'proselytizing ban', 'evangelism restriction'
            ]
        }
        
        # European missionary impact keywords
        self.european_missionary_impact = {
            'direct_impact': [
                'european missionary', 'european church', 'european christian',
                'western missionary', 'european aid worker', 'european religious',
                'european charity', 'european ngo', 'european humanitarian',
                'eu missionary', 'german missionary', 'british missionary',
                'french missionary', 'italian missionary', 'spanish missionary',
                'dutch missionary', 'scandinavian missionary', 'nordic missionary'
            ],
            'policy_impact': [
                'religious visa', 'missionary visa', 'religious worker visa',
                'foreign religious', 'foreign missionary', 'religious registration',
                'church registration', 'religious organization law', 'foreign agent law',
                'foreign funding', 'foreign donation', 'religious extremism law',
                'anti-proselytizing', 'anti-conversion', 'religious propaganda',
                'religious education restriction', 'religious publishing restriction'
            ],
            'security_impact': [
                'kidnapping', 'hostage', 'evacuation', 'embassy warning', 'travel advisory',
                'security threat', 'terrorist threat', 'extremist threat', 'civil unrest',
                'political instability', 'border closure', 'regional conflict',
                'religious violence', 'targeted attack', 'foreign national', 'westerner',
                'european citizen', 'eu citizen', 'diplomatic tension'
            ],
            'global_trends': [
                'religious freedom decline', 'persecution increase', 'missionary access',
                'humanitarian access', 'visa restriction trend', 'religious nationalism',
                'religious extremism rise', 'secularization', 'anti-western sentiment',
                'anti-christian sentiment', 'religious polarization', 'geopolitical tension',
                'refugee crisis', 'migration crisis', 'diplomatic relations'
            ]
        }
        
        # Region keywords for geographic focus
        self.region_keywords = {
            'middle_east': [
                'middle east', 'saudi', 'iran', 'iraq', 'syria', 'jordan', 'israel',
                'palestine', 'lebanon', 'turkey', 'yemen', 'oman', 'qatar', 'bahrain',
                'uae', 'united arab emirates', 'kuwait'
            ],
            'asia': [
                'china', 'north korea', 'vietnam', 'laos', 'myanmar', 'burma',
                'thailand', 'cambodia', 'malaysia', 'indonesia', 'philippines',
                'india', 'pakistan', 'bangladesh', 'nepal', 'bhutan', 'sri lanka',
                'maldives', 'japan', 'mongolia', 'taiwan', 'hong kong', 'singapore'
            ],
            'africa': [
                'nigeria', 'somalia', 'sudan', 'south sudan', 'ethiopia', 'eritrea',
                'egypt', 'libya', 'algeria', 'morocco', 'tunisia', 'mali', 'niger',
                'chad', 'central african republic', 'cameroon', 'kenya', 'tanzania',
                'uganda', 'rwanda', 'burundi', 'democratic republic of congo',
                'mozambique', 'zimbabwe', 'south africa'
            ],
            'central_asia': [
                'kazakhstan', 'uzbekistan', 'turkmenistan', 'kyrgyzstan', 'tajikistan',
                'afghanistan', 'pakistan'
            ],
            'europe': [
                # Eastern Europe
                'russia', 'ukraine', 'belarus', 'moldova', 'georgia', 'armenia',
                'azerbaijan', 'turkey', 
                # Balkans
                'greece', 'balkans', 'serbia', 'kosovo', 'albania', 'north macedonia', 
                'bulgaria', 'romania', 'hungary', 'croatia', 'slovenia', 'bosnia', 
                'herzegovina', 'montenegro',
                # Western Europe
                'france', 'germany', 'uk', 'united kingdom', 'britain', 'england', 
                'scotland', 'wales', 'northern ireland', 'ireland', 'spain', 'portugal', 
                'italy', 'vatican', 'belgium', 'netherlands', 'luxembourg',
                # Northern Europe
                'sweden', 'norway', 'denmark', 'finland', 'iceland', 'estonia', 
                'latvia', 'lithuania',
                # Central Europe
                'poland', 'czech', 'slovakia', 'austria', 'switzerland', 'liechtenstein',
                # General European terms
                'european union', 'eu', 'europe', 'schengen', 'eurozone', 'brussels'
            ],
            'latin_america': [
                'mexico', 'cuba', 'venezuela', 'colombia', 'ecuador', 'peru',
                'bolivia', 'chile', 'argentina', 'brazil', 'guatemala', 'el salvador',
                'honduras', 'nicaragua', 'costa rica', 'panama'
            ]
        }
        
        # Europe-specific threat keywords
        self.europe_threat_keywords = {
            'high': [
                'terror', 'attack', 'bombing', 'stabbing', 'shooting', 'riot', 
                'violent protest', 'far-right', 'neo-nazi', 'extremism', 'antisemitism',
                'islamophobia', 'xenophobia', 'hate crime', 'deportation', 'trafficking',
                'migrant crisis', 'refugee crisis'
            ],
            'medium': [
                'secularism', 'religious restrictions', 'anti-religion', 'nationalism', 
                'populism', 'political tension', 'protest', 'demonstration', 'strike',
                'civil unrest', 'anti-christian', 'anti-missionary', 'visa restriction',
                'border control', 'religious registration', 'church registration'
            ],
            'low': [
                'political change', 'election', 'referendum', 'regulation', 'legislation',
                'religious law', 'secular law', 'church state', 'religious education',
                'religious symbol', 'cross ban', 'religious dress', 'proselytizing',
                'evangelism restriction', 'public preaching'
            ]
        }
        
        # Initialize NLTK sentiment analyzer
        try:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        except Exception as e:
            logger.error(f"Failed to initialize sentiment analyzer: {e}")
            self.sentiment_analyzer = None
    
    def assess_threat_level(self, text: str) -> float:
        """Assess threat level on a scale of 0-10 based on content"""
        if not text:
            return 0.0
        
        text = text.lower()
        
        # Count keyword occurrences by category
        high_count = sum(1 for keyword in self.threat_keywords['high'] if keyword in text)
        medium_count = sum(1 for keyword in self.threat_keywords['medium'] if keyword in text)
        low_count = sum(1 for keyword in self.threat_keywords['low'] if keyword in text)
        
        # Check for Europe-specific keywords if any European region is mentioned
        is_europe_related = any(keyword in text for keyword in self.region_keywords['europe'])
        if is_europe_related:
            high_count += sum(1 for keyword in self.europe_threat_keywords['high'] if keyword in text)
            medium_count += sum(1 for keyword in self.europe_threat_keywords['medium'] if keyword in text)
            low_count += sum(1 for keyword in self.europe_threat_keywords['low'] if keyword in text)
        
        # Calculate weighted threat score
        threat_score = (high_count * 3) + (medium_count * 1.5) + (low_count * 0.5)
        
        # Normalize to 0-10 scale
        normalized_score = min(10, threat_score * 1.2)
        
        # Include sentiment analysis if available
        if self.sentiment_analyzer:
            sentiment = self.sentiment_analyzer.polarity_scores(text)
            # Negative sentiment increases threat level
            if sentiment['compound'] < -0.2:
                # Adjust score based on negativity (more negative = higher threat)
                sentiment_factor = abs(sentiment['compound']) * 2
                normalized_score = min(10, normalized_score + sentiment_factor)
        
        return round(normalized_score, 1)
    
    def assess_missionary_relevance(self, text: str) -> float:
        """Assess missionary relevance on a scale of 0-10"""
        if not text:
            return 0.0
        
        text = text.lower()
        
        # Count keyword occurrences by category
        direct_count = sum(1 for keyword in self.missionary_keywords['direct'] if keyword in text)
        indirect_count = sum(1 for keyword in self.missionary_keywords['indirect'] if keyword in text)
        opportunity_count = sum(1 for keyword in self.missionary_keywords['opportunity'] if keyword in text)
        persecution_count = sum(1 for keyword in self.missionary_keywords['persecution'] if keyword in text)
        
        # Check for European missionary impact
        european_impact = self.assess_european_missionary_impact(text)
        
        # Calculate weighted relevance score
        relevance_score = (direct_count * 3) + (indirect_count * 1.5) + \
                         (opportunity_count * 1) + (persecution_count * 2)
        
        # Boost score if there's European missionary impact
        if european_impact > 0:
            relevance_score += european_impact * 1.5
        
        # Normalize to 0-10 scale
        normalized_score = min(10, relevance_score * 1.2)
        
        return round(normalized_score, 1)
        
    def assess_european_missionary_impact(self, text: str) -> float:
        """Assess specific impact on European missionaries on a scale of 0-10"""
        if not text:
            return 0.0
            
        text = text.lower()
        
        # Count keyword occurrences by category
        direct_impact = sum(1 for keyword in self.european_missionary_impact['direct_impact'] if keyword in text)
        policy_impact = sum(1 for keyword in self.european_missionary_impact['policy_impact'] if keyword in text)
        security_impact = sum(1 for keyword in self.european_missionary_impact['security_impact'] if keyword in text)
        global_trends = sum(1 for keyword in self.european_missionary_impact['global_trends'] if keyword in text)
        
        # Calculate weighted impact score
        impact_score = (direct_impact * 3) + (policy_impact * 2.5) + \
                      (security_impact * 2) + (global_trends * 1)
        
        # Normalize to 0-10 scale
        normalized_score = min(10, impact_score * 1.2)
        
        return round(normalized_score, 1)
    
    async def process_intelligence_item(self, item: IntelligenceItem) -> IntelligenceItem:
        """Process a single intelligence item to extract insights"""
        # Assess threat level
        item.threat_level = self.assess_threat_level(item.content)
        
        # Assess missionary relevance
        item.missionary_relevance = self.assess_missionary_relevance(item.content)
        
        # Determine region
        item.region = await self.determine_region(item.content)
        
        # Extract keywords
        keywords = []
        for category in self.threat_keywords.values():
            for keyword in category:
                if keyword.lower() in item.content.lower():
                    keywords.append(keyword)
        
        # Add missionary keywords
        for category in self.missionary_keywords.values():
            for keyword in category:
                if keyword.lower() in item.content.lower():
                    keywords.append(keyword)
        
        # Remove duplicates and update item
        item.keywords = list(set(keywords))
        
        # Extract location if possible (simple approach)
        location_match = re.search(r'in ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', item.content)
        if location_match:
            item.location = location_match.group(1)
            
            # Geocode the location to get coordinates
            latitude, longitude = self.geocode_location(item.location)
            item.latitude = latitude
            item.longitude = longitude
        
        # Calculate sentiment score if analyzer is available
        if hasattr(self, 'sentiment_analyzer') and self.sentiment_analyzer:
            sentiment = self.sentiment_analyzer.polarity_scores(item.content)
            item.sentiment_score = sentiment['compound']
        
        # Set confidence level based on source reliability and content quality
        item.confidence = self.calculate_confidence(item)
        
        # Assess European missionary impact
        european_impact = self.assess_european_missionary_impact(item.content)
        if european_impact > 0:
            # Add European missionary impact to keywords
            if isinstance(item.keywords, dict):
                item.keywords['european_missionary_impact'] = european_impact
            elif isinstance(item.keywords, list):
                item.keywords.append('european_missionary_impact')
            
            # Log items with European missionary impact
            logger.info(f"European missionary impact detected: {item.title} (Impact: {european_impact}, Threat: {item.threat_level})")
        
        # Log high threat items
        if item.threat_level >= 7.0:
            logger.warning(f"High threat intelligence detected: {item.title} (Level: {item.threat_level})")
        
        return item
    
    def update_intelligence_item(self, item: IntelligenceItem) -> bool:
        """Update an existing intelligence item"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert keywords list to JSON string
            keywords_json = json.dumps(item.keywords)
            
            # Convert investigation data dict to JSON string
            investigation_data_json = json.dumps(item.investigation_data)
            
            # Update in database
            cursor.execute('''
                UPDATE intelligence_items SET
                title = ?, content = ?, source = ?, url = ?,
                threat_level = ?, missionary_relevance = ?,
                region = ?, location = ?, latitude = ?, longitude = ?, keywords = ?,
                sentiment_score = ?, confidence = ?,
                investigation_status = ?, investigation_data = ?
                WHERE id = ?
            ''', (
                item.title, item.content, item.source, item.url,
                item.threat_level, item.missionary_relevance,
                item.region, item.location, item.latitude, item.longitude, keywords_json,
                item.sentiment_score, item.confidence, 
                item.investigation_status, investigation_data_json,
                item.id
            ))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error updating intelligence item: {e}")
            return False
    
    async def process_intelligence_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, List[IntelligenceItem]]:
        """Process multiple intelligence sources"""
        results = {}
        
        # Initialize navigator if needed
        if not self.navigator:
            if not await self.initialize_navigator():
                return results
        
        # Process each source
        for source in sources:
            source_name = source.get('name', 'Unknown')
            source_url = source.get('url', '')
            source_type = source.get('type', 'website')
            
            if not source_url:
                continue
            
            try:
                # Process based on source type
                if source_type == 'rss':
                    items = await self.collect_from_rss(source_url, source_name)
                    results[source_name] = items
                elif source_type == 'website':
                    item = await self.collect_from_website(source_url, source_name)
                    if item:
                        results[source_name] = [item]
                
                # Update source last checked timestamp
                self.update_source_timestamp(source_name, source_url)
                
            except Exception as e:
                logger.error(f"Error processing source {source_name}: {e}")
        
        return results
    
    def update_source_timestamp(self, name: str, url: str) -> None:
        """Update the last checked timestamp for a source"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if source exists
            cursor.execute('''
                SELECT id FROM sources WHERE name = ? AND url = ?
            ''', (name, url))
            
            source = cursor.fetchone()
            
            if source:
                # Update existing source
                cursor.execute('''
                    UPDATE sources SET last_collected_at = ? WHERE id = ?
                ''', (datetime.now().isoformat(), source[0]))
            else:
                # Insert new source with required fields matching the schema
                cursor.execute('''
                    INSERT INTO sources (name, url, source_type, reliability_score, language, last_collected_at, is_active, collection_frequency, rate_limit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, url, 'rss', 0.5, 'en', datetime.now().isoformat(), 1, 3600, 0))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating source timestamp: {e}")
    
    async def determine_region(self, text: str) -> Optional[str]:
        """Determine the region mentioned in the text"""
        if not text:
            return None
            
        text = text.lower()
        
        # Define regions and their associated keywords
        regions = {
            'Europe': ['europe', 'european', 'eu', 'euro', 'brussels', 'germany', 'france', 'italy', 'spain', 
                      'uk', 'britain', 'england', 'scotland', 'ireland', 'poland', 'hungary', 'sweden', 
                      'norway', 'finland', 'denmark', 'netherlands', 'belgium', 'austria', 'switzerland', 
                      'greece', 'portugal', 'czech', 'slovakia', 'romania', 'bulgaria', 'croatia', 'serbia', 
                      'bosnia', 'albania', 'montenegro', 'macedonia', 'kosovo', 'ukraine', 'belarus', 'moldova', 
                      'baltic', 'estonia', 'latvia', 'lithuania', 'vatican', 'holy see'],
            'Middle East': ['middle east', 'israel', 'palestine', 'gaza', 'west bank', 'jerusalem', 'syria', 
                          'lebanon', 'jordan', 'iraq', 'iran', 'saudi', 'yemen', 'oman', 'qatar', 'bahrain', 
                          'kuwait', 'uae', 'united arab emirates', 'turkey', 'egypt'],
            'Africa': ['africa', 'north africa', 'sub-saharan', 'sahel', 'nigeria', 'ethiopia', 'kenya', 
                      'tanzania', 'uganda', 'rwanda', 'burundi', 'congo', 'drc', 'sudan', 'south sudan', 
                      'eritrea', 'somalia', 'djibouti', 'mozambique', 'zimbabwe', 'south africa'],
            'Asia': ['asia', 'china', 'japan', 'korea', 'north korea', 'south korea', 'mongolia', 'taiwan', 
                    'hong kong', 'macau', 'philippines', 'indonesia', 'malaysia', 'singapore', 'thailand', 
                    'vietnam', 'cambodia', 'laos', 'myanmar', 'burma', 'bangladesh', 'india', 'pakistan', 
                    'sri lanka', 'nepal', 'bhutan', 'afghanistan', 'kazakhstan', 'uzbekistan', 'turkmenistan', 
                    'kyrgyzstan', 'tajikistan'],
            'Americas': ['america', 'united states', 'usa', 'canada', 'mexico', 'central america', 'caribbean', 
                        'south america', 'latin america', 'brazil', 'argentina', 'chile', 'peru', 'colombia', 
                        'venezuela', 'ecuador', 'bolivia', 'paraguay', 'uruguay', 'guyana', 'suriname', 
                        'french guiana', 'panama', 'costa rica', 'nicaragua', 'honduras', 'el salvador', 
                        'guatemala', 'belize', 'cuba', 'haiti', 'dominican republic', 'jamaica', 'bahamas', 
                        'puerto rico'],
            'Oceania': ['oceania', 'australia', 'new zealand', 'papua new guinea', 'fiji', 'solomon islands', 
                       'vanuatu', 'samoa', 'tonga', 'micronesia', 'polynesia', 'melanesia', 'marshall islands', 
                       'palau', 'nauru', 'kiribati', 'tuvalu']
        }
        
        # Count occurrences of region keywords
        region_counts = {}
        for region, keywords in regions.items():
            count = sum(1 for keyword in keywords if keyword in text)
            if count > 0:
                region_counts[region] = count
        
        # Return the region with the most keyword occurrences
        if region_counts:
            return max(region_counts.items(), key=lambda x: x[1])[0]
        
        return None
        
    def geocode_location(self, location_name: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocode a location name to get coordinates
        
        Args:
            location_name: Name of the location to geocode
            
        Returns:
            Tuple of (latitude, longitude) or (None, None) if geocoding fails
        """
        if not location_name:
            return None, None
            
        try:
            # Simple mock geocoding for now
            # In a real system, this would use a geocoding service
            if 'paris' in location_name.lower():
                return 48.8566, 2.3522
            elif 'london' in location_name.lower():
                return 51.5074, -0.1278
            elif 'berlin' in location_name.lower():
                return 52.5200, 13.4050
            elif 'rome' in location_name.lower():
                return 41.9028, 12.4964
            elif 'madrid' in location_name.lower():
                return 40.4168, -3.7038
            else:
                # Return None for unknown locations
                return None, None
            
            latitude = float(result["lat"])
            longitude = float(result["lon"])
            
            logger.debug(f"Geocoded {location_name} to {latitude}, {longitude}")
            
            return latitude, longitude
            
        except Exception as e:
            logger.error(f"Error geocoding location {location_name}: {e}")
            return None, None
    
    def calculate_confidence(self, item: IntelligenceItem) -> float:
        """Calculate confidence score for an intelligence item
        
        Args:
            item: The intelligence item to calculate confidence for
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence starts at 0.5
        confidence = 0.5
        
        # Adjust based on source reliability
        reliable_sources = ['bbc', 'reuters', 'associated press', 'al jazeera', 'cnn']
        for source in reliable_sources:
            if source.lower() in item.source.lower():
                confidence += 0.1
                break
        
        # Adjust based on content quality
        if len(item.content) > 200:  # Longer content may be more reliable
            confidence += 0.1
            
        if item.keywords and len(item.keywords) > 3:  # More keywords suggest more relevant content
            confidence += 0.1
            
        # Adjust based on location data
        if item.location and item.latitude and item.longitude:
            confidence += 0.1
            
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def close(self):
        """Close any resources"""
        pass


class StealthWebNavigator:
    """Stealth web navigation capabilities to avoid detection"""
    
    def __init__(self, headless: bool = True):
        self.browser = None
        self.page = None
        self.context = None
        self.headless = headless
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        ]
    
    async def initialize(self) -> bool:
        """Initialize the browser and page"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            # Create a context with random user agent
            user_agent = random.choice(self.user_agents)
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='Europe/London',
                geolocation={'longitude': 0, 'latitude': 51.5},
                permissions=['geolocation']
            )
            
            # Create a new page
            self.page = await self.context.new_page()
            
            # Set various evasion techniques
            await self._set_evasion_techniques()
            
            logger.info("StealthWebNavigator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize StealthWebNavigator: {e}")
            return False
    
    async def _set_evasion_techniques(self):
        """Set various evasion techniques to avoid detection"""
        # Randomize navigator properties
        await self.page.evaluate("""
            () => {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            }
        """)
    
    async def navigate(self, url: str) -> str:
        """Navigate to a URL and return the page content"""
        if not self.page:
            logger.error("Browser not initialized")
            return ""
        
        try:
            # Add random delay to mimic human behavior
            await asyncio.sleep(random.uniform(1, 3))
            
            # Navigate to the URL
            response = await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            if not response:
                logger.warning(f"Failed to get response from {url}")
                return ""
                
            if response.status >= 400:
                logger.warning(f"Error response {response.status} from {url}")
                return ""
            
            # Wait for content to load
            await self.page.wait_for_load_state('networkidle')
            
            # Extract content
            content = await self.page.content()
            
            # Add random delay after navigation
            await asyncio.sleep(random.uniform(2, 5))
            
            return content
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return ""
    
    async def extract_text(self, selector: str) -> str:
        """Extract text from a specific element on the page"""
        if not self.page:
            return ""
            
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content()
            return ""
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    async def close(self):
        """Close the browser and release resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
                
            logger.info("StealthWebNavigator closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing StealthWebNavigator: {e}")


class IntelligenceCollector:
    """Collects and processes intelligence from various sources"""
    
    def __init__(self, db_path: str = 'data/intelligence.db'):
        self.db_path = db_path
        self.navigator = None
        self.analyzer = MissionaryThreatAssessment(db_path=db_path)
        self.sentiment_analyzer = None
        
        # Initialize sentiment analyzer if NLTK is available
        try:
            nltk.data.find('vader_lexicon')
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        except LookupError:
            logger.warning("NLTK Vader lexicon not found. Sentiment analysis will be disabled.")
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize the SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS intelligence_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    threat_level REAL DEFAULT 0.0,
                    missionary_relevance REAL DEFAULT 0.0,
                    region TEXT,
                    location TEXT,
                    latitude REAL,
                    longitude REAL,
                    keywords TEXT,
                    sentiment_score REAL DEFAULT 0.0,
                    confidence REAL DEFAULT 0.0,
                    investigation_status TEXT DEFAULT 'pending',
                    investigation_data TEXT
                )
            ''')
            
            # Create source tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS source_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    last_checked TIMESTAMP,
                    status TEXT,
                    items_collected INTEGER DEFAULT 0
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    async def initialize_navigator(self, headless: bool = True) -> bool:
        """Initialize the web navigator"""
        self.navigator = StealthWebNavigator(headless=headless)
        return await self.navigator.initialize()
    
    async def collect_from_url(self, source_name: str, url: str, source_type: str = 'rss', source_config: Dict = None) -> List[IntelligenceItem]:
        """Collect intelligence from a specific URL
        
        Args:
            source_name: Name of the intelligence source
            url: URL to collect from
            source_type: Type of source (rss, api, web)
            source_config: Additional configuration for the source
        
        Returns:
            List of intelligence items collected
        """
        items = []
        source_config = source_config or {}
        
        try:
            if source_type == 'api':
                # Handle API sources
                items = await self._collect_from_api(source_name, url, source_config)
            elif source_type == 'web':
                # Handle web scraping with specific configuration
                if not self.navigator:
                    logger.error("Web navigator not initialized")
                    return items
                
                content = await self.navigator.navigate(url)
                if not content:
                    return items
                
                items = self._parse_web_page(source_name, url, content, source_config.get('scrape_config', {}))
            else:
                # Handle RSS feeds and standard web pages
                if not self.navigator:
                    logger.error("Web navigator not initialized")
                    return items
                
                content = await self.navigator.navigate(url)
                if not content:
                    return items
                
                # Parse content based on URL type
                if 'rss' in url or 'feed' in url or 'xml' in url:
                    items = self._parse_rss_feed(source_name, url, content)
                else:
                    items = self._parse_html_page(source_name, url, content)
        
            # Process each item
            processed_items = []
            for item in items:
                try:
                    processed_item = await self.analyzer.process_intelligence_item(item)
                    processed_items.append(processed_item)
                except Exception as e:
                    logger.error(f"Error processing item from {source_name}: {e}")
        
            # Update source tracking
            self.analyzer.update_source_timestamp(source_name, url)
        
            # Store in database
            self._store_intelligence_items(processed_items)
        
            return processed_items
        
        except Exception as e:
            logger.error(f"Error collecting from {url}: {e}")
            return items
    
    def _parse_rss_feed(self, source_name: str, url: str, content: str) -> List[IntelligenceItem]:
        """Parse RSS feed content"""
        items = []
        
        try:
            feed = feedparser.parse(content)
            
            for entry in feed.entries[:10]:  # Limit to 10 items
                item = IntelligenceItem(
                    title=entry.get('title', ''),
                    content=entry.get('description', ''),
                    source=source_name,
                    url=entry.get('link', url)
                )
                items.append(item)
                
        except Exception as e:
            logger.error(f"Error parsing RSS feed {url}: {e}")
            
        return items
    
    def _parse_html_page(self, source_name: str, url: str, content: str) -> List[IntelligenceItem]:
        """Parse HTML page content"""
        items = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            title = soup.title.text.strip() if soup.title else url
            
            # Extract main content
            main_content = ""
            main_tags = soup.find_all(['article', 'main', 'div', 'section'], class_=re.compile('content|article|main|body'))
            if main_tags:
                main_content = main_tags[0].get_text(separator=' ', strip=True)
            else:
                # Fallback to body content
                body = soup.find('body')
                if body:
                    main_content = body.get_text(separator=' ', strip=True)[:5000]  # Limit to 5000 chars
            
            # Extract publication date if available
            pub_date = None
            date_tags = soup.find_all(['time', 'span', 'div', 'p'], class_=re.compile('date|time|published'))
            for tag in date_tags:
                if tag.get('datetime'):
                    pub_date = tag.get('datetime')
                    break
                elif tag.text and re.search(r'\d{1,2}\s+\w+\s+\d{4}', tag.text):
                    pub_date = tag.text.strip()
                    break
            
            # Create intelligence item
            if main_content:
                item = IntelligenceItem(
                    title=title,
                    content=main_content,
                    source=source_name,
                    url=url,
                    collection_date=datetime.now().isoformat(),
                    publication_date=pub_date
                )
                items.append(item)
            
        except Exception as e:
            logger.error(f"Error parsing HTML page {url}: {e}")
        
        return items
        
    def _parse_web_page(self, source_name: str, url: str, content: str, scrape_config: Dict) -> List[IntelligenceItem]:
        """Parse web page with specific scraping configuration
        
        Args:
            source_name: Name of the intelligence source
            url: URL of the page
            content: HTML content of the page
            scrape_config: Configuration for scraping (elements, title, content, date selectors)
            
        Returns:
            List of intelligence items extracted
        """
        items = []
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Get element selector
            element_selector = scrape_config.get('elements', 'article')
            elements = soup.select(element_selector)
            
            # Get field selectors
            title_selector = scrape_config.get('title', 'h2')
            content_selector = scrape_config.get('content', 'p')
            date_selector = scrape_config.get('date', 'time')
            
            for element in elements:
                try:
                    # Extract title
                    title_elem = element.select_one(title_selector)
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                    
                    # Extract content
                    content_elem = element.select_one(content_selector)
                    content_text = content_elem.get_text(strip=True) if content_elem else ""
                    
                    # Extract date
                    date_elem = element.select_one(date_selector)
                    pub_date = None
                    if date_elem:
                        if date_elem.get('datetime'):
                            pub_date = date_elem.get('datetime')
                        else:
                            pub_date = date_elem.get_text(strip=True)
                    
                    # Create intelligence item if we have content
                    if content_text:
                        item = IntelligenceItem(
                            title=title,
                            content=content_text,
                            source=source_name,
                            url=url,
                            collection_date=datetime.now().isoformat(),
                            publication_date=pub_date
                        )
                        items.append(item)
                except Exception as e:
                    logger.error(f"Error parsing element from {url}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing web page with config {url}: {e}")
        
        return items
        
    async def _collect_from_api(self, source_name: str, url: str, source_config: Dict) -> List[IntelligenceItem]:
        """Collect intelligence from an API source
        
        Args:
            source_name: Name of the intelligence source
            url: API URL
            source_config: Configuration for the API (headers, params, etc.)
            
        Returns:
            List of intelligence items collected
        """
        items = []
        
        try:
            # Set up API request parameters
            headers = source_config.get('headers', {})
            params = source_config.get('query_params', {})
            api_key_required = source_config.get('api_key_required', False)
            api_key_env = source_config.get('api_key_env', '')
            api_key_header = source_config.get('api_key_header', 'Authorization')
            api_key_prefix = source_config.get('api_key_prefix', 'Bearer ')
            
            # Add API key if required
            if api_key_required and api_key_env:
                api_key = os.environ.get(api_key_env)
                if api_key:
                    headers[api_key_header] = f"{api_key_prefix}{api_key}"
                else:
                    logger.warning(f"API key environment variable {api_key_env} not found for {source_name}")
            
            # Make async API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract items based on response format
                        item_path = source_config.get('item_path', '')
                        if item_path:
                            # Navigate to the items in the response
                            items_data = data
                            for key in item_path.split('.'):
                                if key in items_data:
                                    items_data = items_data[key]
                                else:
                                    items_data = []
                                    break
                        else:
                            # Assume the response is the items or contains an 'items' field
                            items_data = data.get('items', data.get('data', data))
                        
                        # Ensure items_data is a list
                        if not isinstance(items_data, list):
                            items_data = [items_data]
                        
                        # Map fields from API response to intelligence items
                        field_mapping = source_config.get('field_mapping', {
                            'title': ['title', 'headline', 'name'],
                            'content': ['content', 'description', 'body', 'text'],
                            'date': ['date', 'published', 'created', 'timestamp'],
                            'url': ['url', 'link'],
                            'location': ['location', 'place', 'geo']
                        })
                        
                        for item_data in items_data:
                            # Extract fields using mapping
                            title = self._extract_field(item_data, field_mapping.get('title', []))
                            content = self._extract_field(item_data, field_mapping.get('content', []))
                            date = self._extract_field(item_data, field_mapping.get('date', []))
                            item_url = self._extract_field(item_data, field_mapping.get('url', []))
                            location = self._extract_field(item_data, field_mapping.get('location', []))
                            
                            # Create intelligence item if we have content
                            if title or content:
                                item = IntelligenceItem(
                                    title=title or "API Item",
                                    content=content or title,
                                    source=source_name,
                                    url=item_url or url,
                                    collection_date=datetime.now().isoformat(),
                                    publication_date=date,
                                    location=location
                                )
                                items.append(item)
                    else:
                        logger.warning(f"Error response {response.status} from {url}")
            
        except Exception as e:
            logger.error(f"Error collecting from API {url}: {e}")
        
        return items
    
    def _extract_field(self, data: Dict, field_keys: List[str]) -> str:
        """Extract a field from a dictionary using multiple possible keys
        
        Args:
            data: Dictionary to extract from
            field_keys: List of possible keys to try
            
        Returns:
            Extracted value or empty string
        """
        for key in field_keys:
            if key in data and data[key]:
                return str(data[key])
        return ""
    
    def _store_intelligence_items(self, items: List[IntelligenceItem]) -> None:
        """Store intelligence items in the database"""
        if not items:
            return
            
        try:
            # Filter items for European or missionary relevance
            europe_filter = EuropeFilter()
            filtered_items = []
            
            for item in items:
                # Convert item to dictionary for filtering
                item_dict = item.to_dict()
                
                # Only keep items relevant to Europe or European missionaries
                if europe_filter.is_relevant(item_dict):
                    filtered_items.append(item)
                    logger.info(f"Keeping item relevant to Europe/missionaries: {item_dict['title']}")
                else:
                    logger.debug(f"Filtering out non-European item: {item_dict['title']}")
            
            logger.info(f"Filtered {len(items)} items to {len(filtered_items)} Europe/missionary relevant items")
            
            # If no items remain after filtering, return early
            if not filtered_items:
                return
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for item in filtered_items:
                # Convert item to dictionary
                item_dict = item.to_dict()
                
                # Check if item already exists
                cursor.execute(
                    'SELECT id FROM intelligence_items WHERE title = ? AND source = ?',
                    (item_dict['title'], item_dict['source'])
                )
                
                existing = cursor.fetchone()
                if existing:
                    # Skip duplicate items
                    continue
                    
                # Insert new item
                cursor.execute('''
                    INSERT INTO intelligence_items (
                        title, content, source, url, timestamp, threat_level, missionary_relevance,
                        region, location, latitude, longitude, keywords, sentiment_score, confidence,
                        investigation_status, investigation_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_dict['title'], item_dict['content'], item_dict['source'], item_dict['url'],
                    item_dict['timestamp'], item_dict['threat_level'], item_dict['missionary_relevance'],
                    item_dict['region'], item_dict['location'], item_dict['latitude'], item_dict['longitude'],
                    json.dumps(item_dict['keywords']), item_dict['sentiment_score'], item_dict['confidence'],
                    item_dict.get('investigation_status', 'pending'), json.dumps(item_dict.get('investigation_data', {}))
                ))
                
                # Get the inserted ID
                item.id = cursor.lastrowid
                logger.debug(f"Stored new intelligence item: {item_dict['title']}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing intelligence items: {e}")
    
    async def process_intelligence_sources(self, sources: List[Dict[str, Any]]) -> List[IntelligenceItem]:
        """Process multiple intelligence sources"""
        all_items = []
        
        if not self.navigator:
            logger.error("Web navigator not initialized")
            return all_items
            
        for source in sources:
            name = source.get('name', 'Unknown')
            url = source.get('url', '')
            enabled = source.get('enabled', True)
            source_type = source.get('type', 'rss')
            reliability = source.get('reliability', 5) / 10.0  # Convert 0-10 scale to 0-1
            
            if not enabled or not url:
                continue
                
            logger.info(f"Processing source: {name} ({url}) - Type: {source_type}")
            
            try:
                # Create source config dictionary
                source_config = {
                    'reliability_score': reliability,
                    'api_key_required': source.get('api_key_required', False),
                    'api_key_env': source.get('api_key_env', ''),
                    'query_params': source.get('query_params', {}),
                    'headers': source.get('headers', {}),
                    'scrape_config': source.get('scrape_config', {}),
                    'field_mapping': source.get('field_mapping', {})
                }
                
                # Collect from source based on type
                items = await self.collect_from_url(name, url, source_type, source_config)
                all_items.extend(items)
                logger.info(f"Collected {len(items)} items from {name}")
            except Exception as e:
                logger.error(f"Error processing source {name}: {e}")
                
        return all_items
    
    def get_high_threat_intelligence(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get high threat intelligence items"""
        items = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM intelligence_items 
                WHERE threat_level >= 7.0 AND missionary_relevance >= 5.0
                ORDER BY threat_level DESC, timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                item = dict(row)
                # Parse JSON fields
                item['keywords'] = json.loads(item['keywords']) if item['keywords'] else []
                item['investigation_data'] = json.loads(item['investigation_data']) if item['investigation_data'] else {}
                items.append(item)
            
            conn.close()
            
            # Ensure items are relevant to Europe or European missionaries
            # This is a redundant check since we already filter when storing,
            # but it ensures consistency if the filtering logic changes
            items = filter_intelligence(items)
            
        except Exception as e:
            logger.error(f"Error getting high threat intelligence: {e}")
            
        return items
    
    def get_recent_intelligence(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent intelligence items"""
        items = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM intelligence_items 
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            
            for row in rows:
                item = dict(row)
                # Parse JSON fields
                item['keywords'] = json.loads(item['keywords']) if item['keywords'] else []
                item['investigation_data'] = json.loads(item['investigation_data']) if item['investigation_data'] else {}
                items.append(item)
            
            conn.close()
            
            # Ensure items are relevant to Europe or European missionaries
            # This is a redundant check since we already filter when storing,
            # but it ensures consistency if the filtering logic changes
            items = filter_intelligence(items)
            
        except Exception as e:
            logger.error(f"Error getting recent intelligence: {e}")
            
        return items
    
    async def investigate_intelligence(self, item: Union[IntelligenceItem, Dict[str, Any]]) -> None:
        """Conduct deeper investigation on an intelligence item"""
        # Convert dict to IntelligenceItem if needed
        if isinstance(item, dict):
            intel_item = IntelligenceItem(
                id=item.get('id'),
                title=item.get('title', ''),
                content=item.get('content', ''),
                source=item.get('source', ''),
                url=item.get('url', ''),
                threat_level=item.get('threat_level', 0.0),
                missionary_relevance=item.get('missionary_relevance', 0.0),
                region=item.get('region'),
                location=item.get('location'),
                keywords=item.get('keywords', []),
                sentiment_score=item.get('sentiment_score', 0.0),
                confidence=item.get('confidence', 0.0),
                investigation_status=item.get('investigation_status', 'pending'),
                investigation_data=item.get('investigation_data', {})
            )
        else:
            intel_item = item
        
        # Skip if already investigated
        if intel_item.investigation_status == 'completed':
            return
        
        # Update status to in_progress
        intel_item.investigation_status = 'in_progress'
        self.analyzer.update_intelligence_item(intel_item)
        
        # Initialize navigator if needed
        if not self.navigator:
            if not await self.initialize_navigator():
                return
        
        try:
            # Navigate to the URL for more information
            if intel_item.url:
                logger.info(f"Investigating intelligence item: {intel_item.title}")
                
                # Get additional content from the URL
                content = await self.navigator.navigate(intel_item.url)
                
                if content:
                    # Parse content
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract main article content
                    article = soup.find(['article', 'div', 'section'], class_=['article', 'news-item', 'post'])
                    if not article:
                        article = soup.find(['main', 'div', 'section'], id=['content', 'main', 'main-content'])
                    if not article:
                        article = soup.body
                    
                    if article:
                        # Extract full content
                        full_content = article.get_text().strip()
                        
                        # Update item with full content if it's more detailed
                        if len(full_content) > len(intel_item.content):
                            intel_item.content = full_content
                            
                            # Re-assess threat level and missionary relevance with full content
                            intel_item.threat_level = self.analyzer.assess_threat_level(full_content)
                            intel_item.missionary_relevance = self.analyzer.assess_missionary_relevance(full_content)
                            
                            # Extract location if available
                            location_elem = article.find(['span', 'div', 'p'], class_=['location', 'dateline'])
                            if location_elem:
                                intel_item.location = location_elem.get_text().strip()
                        
                        # Store investigation data
                        intel_item.investigation_data['full_analysis'] = True
                        intel_item.investigation_data['investigation_timestamp'] = datetime.now().isoformat()
                        
                        # Update confidence level
                        intel_item.confidence = min(10.0, intel_item.confidence + 2.0)
            
            # Update status to completed
            intel_item.investigation_status = 'completed'
            self.analyzer.update_intelligence_item(intel_item)
            
            logger.info(f"Investigation completed for: {intel_item.title}")
            
        except Exception as e:
            logger.error(f"Error investigating intelligence item: {e}")
            # Mark as pending to retry later
            intel_item.investigation_status = 'pending'
            self.analyzer.update_intelligence_item(intel_item)
    
    async def close(self) -> None:
        """Close resources"""
        if self.navigator:
            await self.navigator.close()
    """Main orchestrator for running intelligence cycles, alerts, and monitoring"""
    
    def __init__(self, config_path: str = 'config/settings.json', sources_paths: List[str] = None):
        self.config_path = config_path
        self.sources_paths = sources_paths or ['config/sources.json', 'config/new_sources.json']
        self.config = {}
        self.sources = []
        self.collector = None
        self.running = False
        self.cycle_count = 0
        self.last_cycle_time = None
        self.demo_mode = False
        
        # Initialize system
        self.load_config()
        self.load_sources()
        self.collector = IntelligenceCollector(db_path=self.config.get('database_path', 'data/intelligence.db'))
        
        # Set up signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def load_config(self) -> None:
        """Load system configuration from JSON file"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                logger.error(f"Configuration file not found: {self.config_path}")
                self.config = {}
                return
                
            with open(config_file, 'r') as f:
                self.config = json.load(f)
                
            logger.info(f"Configuration loaded from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = {}
    
    def load_sources(self) -> None:
        """Load intelligence sources from multiple JSON files"""
        try:
            all_sources = []
            
            for source_path in self.sources_paths:
                if not os.path.exists(source_path):
                    logger.warning(f"Sources file not found: {source_path}")
                    continue
                    
                with open(source_path, 'r') as f:
                    data = json.load(f)
                    
                sources = data.get('sources', [])
                all_sources.extend(sources)
                logger.info(f"Loaded {len(sources)} intelligence sources from {source_path}")
            
            if not all_sources:
                logger.error("No intelligence sources loaded from any file")
                return False
                
            self.sources = all_sources
            logger.info(f"Loaded {len(self.sources)} total intelligence sources")
            return True
            
        except Exception as e:
            logger.error(f"Error loading sources: {e}")
            return False
    
    async def initialize(self) -> bool:
        """Initialize the system and its components"""
        try:
            # Initialize the intelligence collector
            if not self.collector:
                self.collector = IntelligenceCollector(db_path=self.config.get('database_path', 'data/intelligence.db'))
            
            # Initialize web navigator
            headless = self.config.get('stealth', {}).get('headless', True)
            if not await self.collector.initialize_navigator(headless=headless):
                logger.error("Failed to initialize web navigator")
                return False
            
            logger.info("Guardian system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing guardian system: {e}")
            return False
    
    async def run_intelligence_cycle(self) -> Dict[str, Any]:
        """Run a complete intelligence collection and analysis cycle"""
        cycle_start = time.time()
        self.cycle_count += 1
        cycle_results = {
            'cycle_id': self.cycle_count,
            'timestamp': datetime.now().isoformat(),
            'sources_processed': 0,
            'items_collected': 0,
            'high_threats': 0,
            'errors': 0,
            'items': []
        }
        
        try:
            logger.info(f"Starting intelligence cycle {self.cycle_count}")
            
            # Process intelligence sources
            results = await self.collector.process_intelligence_sources(self.sources)
            
            # Collect results
            items_collected = 0
            high_threats = 0
            
            for source_name, items in results.items():
                items_collected += len(items)
                
                # Count high threats
                for item in items:
                    if item.threat_level >= 7.0 and item.missionary_relevance >= 5.0:
                        high_threats += 1
                        
                        # Investigate high threats if not in demo mode
                        if not self.demo_mode:
                            await self.collector.investigate_intelligence(item)
                
                # Add to cycle results
                cycle_results['items'].extend([asdict(item) for item in items])
            
            # Update cycle results
            cycle_results['sources_processed'] = len(results)
            cycle_results['items_collected'] = items_collected
            cycle_results['high_threats'] = high_threats

            # Calculate cycle duration
            cycle_duration = time.time() - cycle_start
            self.last_cycle_time = cycle_duration
            cycle_results['duration'] = cycle_duration

            logger.info(f"Completed intelligence cycle {self.cycle_count} in {cycle_duration:.2f}s")
            logger.info(f"Processed {len(results)} sources, collected {items_collected} items, found {high_threats} high threats")

            # Send intelligence items to Sentinel for verification and analysis
            if items_collected > 0 and not self.demo_mode:
                sentinel_result = await self.send_to_sentinel(cycle_results['items'])
                cycle_results['sentinel_status'] = sentinel_result['status']
                cycle_results['sentinel_sent'] = sentinel_result['sent']
                if sentinel_result['status'] == 'success':
                    logger.info(f"Successfully sent {sentinel_result['sent']} items to Sentinel for verification")
                else:
                    logger.warning(f"Sentinel integration: {sentinel_result['message']}")

            return cycle_results

        except Exception as e:
            logger.error(f"Error in intelligence cycle: {e}")
            logger.error(traceback.format_exc())
            cycle_results['errors'] = 1
            cycle_results['error_details'] = str(e)
            return cycle_results
    
    async def run_continuous_monitoring(self, interval_minutes: int = 60) -> None:
        """Run continuous monitoring with specified interval"""
        self.running = True
        
        try:
            # Initialize system
            if not await self.initialize():
                logger.error("Failed to initialize system for continuous monitoring")
                return
            
            logger.info(f"Starting continuous monitoring with {interval_minutes} minute interval")
            
            while self.running:
                # Run intelligence cycle
                await self.run_intelligence_cycle()
                
                # Check for high threats
                high_threats = self.collector.get_high_threat_intelligence()
                if high_threats:
                    logger.warning(f"Found {len(high_threats)} high threat intelligence items")
                    
                    # Process high threats
                    for item in high_threats:
                        # Check if item is a dict or an IntelligenceItem object
                        if isinstance(item, dict):
                            if item.get('investigation_status') == 'pending':
                                logger.info(f"Investigating high threat: {item['title']}")
                                await self.collector.investigate_intelligence(item)
                        else:  # IntelligenceItem object
                            if item.investigation_status == 'pending':
                                logger.info(f"Investigating high threat: {item.title}")
                                await self.collector.investigate_intelligence(item)
                
                # Wait for next cycle if still running
                if self.running:
                    logger.info(f"Waiting {interval_minutes} minutes until next cycle")
                    for _ in range(interval_minutes * 60):
                        if not self.running:
                            break
                        await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
            logger.error(traceback.format_exc())
        
        finally:
            # Cleanup
            if self.collector:
                await self.collector.close()
            
            logger.info("Continuous monitoring stopped")
    
    async def run_demo(self, cycles: int = 1) -> List[Dict[str, Any]]:
        """Run a demo with specified number of cycles"""
        self.demo_mode = True
        results = []
        
        try:
            # Initialize system
            if not await self.initialize():
                logger.error("Failed to initialize system for demo")
                return results
            
            logger.info(f"Starting demo with {cycles} cycles")
            
            # Run specified number of cycles
            for i in range(cycles):
                logger.info(f"Running demo cycle {i+1}/{cycles}")
                cycle_result = await self.run_intelligence_cycle()
                results.append(cycle_result)
                
                # Wait briefly between cycles
                if i < cycles - 1:
                    await asyncio.sleep(2)
            
            logger.info(f"Demo completed with {cycles} cycles")
            return results
            
        except Exception as e:
            logger.error(f"Error in demo: {e}")
            logger.error(traceback.format_exc())
            return results
            
        finally:
            # Cleanup
            self.demo_mode = False
            if self.collector:
                await self.collector.close()
    
    def get_high_threats(self, limit: int = 10) -> List[IntelligenceItem]:
        """Get high threat intelligence items"""
        if not self.collector:
            return []
        
        return self.collector.get_high_threat_intelligence(limit=limit)
    
    def get_recent_intelligence(self, limit: int = 10) -> List[IntelligenceItem]:
        """Get recent intelligence items"""
        if not self.collector:
            return []
        
        return self.collector.get_recent_intelligence(limit=limit)
    
    def stop(self) -> None:
        """Stop the system"""
        logger.info("Stopping guardian system")
        self.running = False
    
    def _handle_shutdown(self, signum, frame) -> None:
        """Handle shutdown signals"""
        logger.info(f"Received shutdown signal {signum}")
        self.stop()
        
    async def send_to_sentinel(self, items: List[Union[IntelligenceItem, Dict[str, Any]]]) -> Dict[str, Any]:
        """Send intelligence items to Sentinel for verification and analysis
        
        This function ensures that all items sent to Sentinel include their complete verification
        information, including source attribution and URL links to original content.
        
        Args:
            items: List of intelligence items to send, either as IntelligenceItem objects or dictionaries
            
        Returns:
            Dict containing the results of the operation
        """
        if not items:
            logger.warning("No items to send to Sentinel")
            return {"status": "warning", "message": "No items to send", "sent": 0}
            
        sentinel_items = []
        missing_verification = []
        
        # Process each item to ensure it has verification information
        for item in items:
            # Convert to dict if it's an IntelligenceItem object
            if isinstance(item, IntelligenceItem):
                item_dict = asdict(item)
            else:
                item_dict = item
                
            # Check for required verification fields
            if not item_dict.get('source'):
                missing_verification.append({"id": item_dict.get('id'), "reason": "missing source"})
                continue
                
            if not item_dict.get('url'):
                missing_verification.append({"id": item_dict.get('id'), "reason": "missing url"})
                continue
            
            # Add verification metadata
            item_dict['verification'] = {
                'source_verified': True,
                'url_verified': True,
                'timestamp': datetime.now().isoformat(),
                'verification_method': 'automated',
                'verification_agent': 'WatchKeeper Guardian'
            }
            
            sentinel_items.append(item_dict)
        
        # Prepare the payload for Sentinel
        payload = {
            'items': sentinel_items,
            'metadata': {
                'sender': 'WatchKeeper Guardian',
                'timestamp': datetime.now().isoformat(),
                'cycle_id': self.cycle_count,
                'total_items': len(sentinel_items)
            }
        }
        
        # Log the operation
        logger.info(f"Sending {len(sentinel_items)} verified intelligence items to Sentinel")
        if missing_verification:
            logger.warning(f"Skipped {len(missing_verification)} items missing verification information")
        
        # Get Sentinel API endpoint and key from environment variables
        sentinel_api_endpoint = os.getenv("SENTINEL_API_ENDPOINT")
        sentinel_api_key = os.getenv("SENTINEL_API_KEY")
        
        # Check if Sentinel API configuration is available
        if not sentinel_api_endpoint or not sentinel_api_key:
            logger.warning("Sentinel API not configured. Skipping API call.")
            return {
                "status": "warning", 
                "message": "Sentinel API not configured. Data prepared but not sent.", 
                "sent": 0,
                "prepared": len(sentinel_items),
                "skipped": len(missing_verification)
            }
        
        # Make the actual API call to Sentinel
        try:
            async with aiohttp.ClientSession() as session:
                logger.debug(f"Sending data to Sentinel API: {sentinel_api_endpoint}")
                async with session.post(
                    sentinel_api_endpoint, 
                    json=payload, 
                    headers={
                        'Authorization': f'Bearer {sentinel_api_key}',
                        'Content-Type': 'application/json'
                    },
                    timeout=30  # 30 second timeout
                ) as response:
                    if response.status == 200 or response.status == 201:
                        result = await response.json()
                        logger.info(f"Successfully sent data to Sentinel API. Response: {result}")
                        return {
                            "status": "success", 
                            "message": f"Sent {len(sentinel_items)} items to Sentinel", 
                            "sent": len(sentinel_items),
                            "skipped": len(missing_verification),
                            "response": result
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send data to Sentinel API. Status: {response.status}, Response: {error_text}")
                        return {
                            "status": "error", 
                            "message": f"Failed to send data to Sentinel API. Status: {response.status}", 
                            "sent": 0,
                            "prepared": len(sentinel_items),
                            "skipped": len(missing_verification),
                            "error": error_text
                        }
        except Exception as e:
            logger.error(f"Exception when sending data to Sentinel API: {e}")
            return {
                "status": "error", 
                "message": f"Exception when sending data to Sentinel API: {str(e)}", 
                "sent": 0,
                "prepared": len(sentinel_items),
                "skipped": len(missing_verification),
                "error": str(e)
            }
        
        return {
            "status": "success", 
            "message": f"Sent {len(sentinel_items)} items to Sentinel", 
            "sent": len(sentinel_items),
            "skipped": len(missing_verification)
        }      
    async def close(self) -> None:
        """Close the system and release resources"""
        self.stop()
        
        if self.collector:
            await self.collector.close()
            
        logger.info("Guardian system closed")
async def main() -> None:
    """Main entry point for the WatchKeeper system"""
    parser = argparse.ArgumentParser(description='WatchKeeper - Autonomous Intelligence System')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode')
    parser.add_argument('--cycles', type=int, default=1, help='Number of intelligence cycles to run in demo mode')
    parser.add_argument('--monitor', action='store_true', help='Run in continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=60, help='Interval in minutes between intelligence cycles')
    args = parser.parse_args()
    
    try:
        # Create guardian system
        guardian = GuardianSystem()
        
        if args.demo:
            # Run in demo mode
            logger.info(f"Running in demo mode with {args.cycles} cycles")
            results = await guardian.run_demo(cycles=args.cycles)
            
            # Display summary
            print("\n" + "="*50)
            print("WATCHKEEPER DEMO SUMMARY")
            print("="*50)
            
            for i, result in enumerate(results):
                print(f"\nCycle {i+1}:")
                print(f"  Sources processed: {result['sources_processed']}")
                print(f"  Items collected: {result['items_collected']}")
                print(f"  High threats: {result['high_threats']}")
                print(f"  Duration: {result.get('duration', 0):.2f} seconds")
                
                # Show high threat items
                if result['high_threats'] > 0:
                    print("\n  HIGH THREAT ITEMS:")
                    for item in result['items']:
                        if item['threat_level'] >= 7.0 and item['missionary_relevance'] >= 5.0:
                            print(f"    - {item['title']} (Threat: {item['threat_level']}, Relevance: {item['missionary_relevance']})")
                            if item['location']:
                                print(f"      Location: {item['location']} ({item['region']})")
            
            print("\n" + "="*50)
            print("Demo completed successfully")
            
        elif args.monitor:
            # Run in continuous monitoring mode
            logger.info(f"Running in continuous monitoring mode with {args.interval} minute interval")
            await guardian.run_continuous_monitoring(interval_minutes=args.interval)
            
        else:
            # Run a single intelligence cycle
            logger.info("Running a single intelligence cycle")
            result = await guardian.run_intelligence_cycle()
            
            # Display summary
            print("\n" + "="*50)
            print("WATCHKEEPER INTELLIGENCE CYCLE SUMMARY")
            print("="*50)
            print(f"Sources processed: {result['sources_processed']}")
            print(f"Items collected: {result['items_collected']}")
            print(f"High threats: {result['high_threats']}")
            print(f"Duration: {result.get('duration', 0):.2f} seconds")
            
            # Show high threat items
            if result['high_threats'] > 0:
                print("\nHIGH THREAT ITEMS:")
                for item in result['items']:
                    if item['threat_level'] >= 7.0 and item['missionary_relevance'] >= 5.0:
                        print(f"  - {item['title']} (Threat: {item['threat_level']}, Relevance: {item['missionary_relevance']})")
                        if item['location']:
                            print(f"    Location: {item['location']} ({item['region']})")
            
            print("\n" + "="*50)
            
            # Close guardian
            await guardian.close()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
        
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        
    finally:
        logger.info("WatchKeeper system shutting down")


if __name__ == "__main__":
    try:
        # Run the main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nWatchKeeper system terminated by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        traceback.print_exc()
