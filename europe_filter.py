#!/usr/bin/env python3
"""
European Intelligence Filter
This module filters intelligence data to only include items relevant to Europe or European missionaries
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.europe_filter')

# European countries and regions
EUROPEAN_COUNTRIES = [
    "albania", "andorra", "armenia", "austria", "azerbaijan", "belarus", "belgium", 
    "bosnia", "herzegovina", "bulgaria", "croatia", "cyprus", "czech", "denmark", 
    "estonia", "finland", "france", "georgia", "germany", "greece", "hungary", 
    "iceland", "ireland", "italy", "kazakhstan", "kosovo", "latvia", "liechtenstein", 
    "lithuania", "luxembourg", "malta", "moldova", "monaco", "montenegro", 
    "netherlands", "north macedonia", "macedonia", "norway", "poland", "portugal", 
    "romania", "russia", "san marino", "serbia", "slovakia", "slovenia", "spain", 
    "sweden", "switzerland", "turkey", "ukraine", "united kingdom", "uk", "britain", 
    "vatican", "holy see"
]

# European regions and sub-regions
EUROPEAN_REGIONS = [
    "europe", "european union", "eu", "balkans", "baltics", "scandinavia", 
    "nordic", "eastern europe", "western europe", "central europe", 
    "southern europe", "northern europe", "mediterranean", "caucasus"
]

# Keywords related to missionaries and religious activities
MISSIONARY_KEYWORDS = [
    "missionary", "missionaries", "mission", "missions", "evangelist", "evangelism",
    "church", "christian", "christianity", "catholic", "protestant", "orthodox",
    "religious freedom", "persecution", "worship", "ministry", "minister", "priest",
    "pastor", "congregation", "convert", "conversion", "baptism", "seminary",
    "theological", "theology", "religious", "religion", "faith", "faithful",
    "believer", "bible", "gospel", "preach", "preacher", "preaching", "disciple",
    "discipleship", "spiritual", "spirituality", "prayer", "worship", "service",
    "fellowship", "outreach", "witness", "witnessing", "testimony"
]

# Global issues that may affect European missionaries
GLOBAL_ISSUES = [
    "terrorism", "refugee", "migration", "human trafficking", "persecution",
    "natural disaster", "earthquake", "flood", "hurricane", "typhoon", "tsunami",
    "pandemic", "epidemic", "outbreak", "disease", "war", "conflict", "hostage",
    "kidnapping", "evacuation", "coup", "revolution", "protest", "demonstration",
    "riot", "unrest", "civil war", "genocide", "ethnic cleansing", "sanctions",
    "travel ban", "travel advisory", "travel warning", "border closure",
    "visa restriction", "deportation", "expulsion", "diplomatic crisis"
]

class EuropeFilter:
    """Filters intelligence data for European or missionary relevance"""
    
    def __init__(self):
        """Initialize the filter"""
        # Compile regex patterns for faster matching
        european_pattern = r'\b(?:' + '|'.join(EUROPEAN_COUNTRIES + EUROPEAN_REGIONS) + r')\b'
        missionary_pattern = r'\b(?:' + '|'.join(MISSIONARY_KEYWORDS) + r')\b'
        global_pattern = r'\b(?:' + '|'.join(GLOBAL_ISSUES) + r')\b'
        
        self.european_regex = re.compile(european_pattern, re.IGNORECASE)
        self.missionary_regex = re.compile(missionary_pattern, re.IGNORECASE)
        self.global_regex = re.compile(global_pattern, re.IGNORECASE)
        
    def is_relevant(self, intelligence_item: Dict[str, Any]) -> bool:
        """
        Determine if an intelligence item is relevant to Europe or European missionaries
        
        Args:
            intelligence_item: Dictionary containing intelligence data
            
        Returns:
            bool: True if relevant, False otherwise
        """
        # Extract text content to search
        title = intelligence_item.get('title', '')
        content = intelligence_item.get('content', '')
        region = intelligence_item.get('region', '')
        country = intelligence_item.get('country', '')
        
        # Combine text for searching
        text = f"{title} {content} {region} {country}".lower()
        
        # Check for European location or mentions
        has_european_relevance = (
            region.lower() == 'europe' or 
            country.lower() in [c.lower() for c in EUROPEAN_COUNTRIES] or
            self.european_regex.search(text) is not None
        )
        
        # If it has direct European relevance, keep it
        if has_european_relevance:
            return True
        
        # Check for missionary relevance, but ONLY if it also has European connection
        missionary_relevance = intelligence_item.get('missionary_relevance', 0)
        has_missionary_relevance = missionary_relevance > 0 or self.missionary_regex.search(text) is not None
        
        # Only keep missionary-relevant items if they also have European relevance
        if has_missionary_relevance and has_european_relevance:
            return True
        
        # Check for global issues that may affect European missionaries
        if self.global_regex.search(text) and has_european_relevance and has_missionary_relevance:
            return True
            
        # Not relevant to Europe or European missionaries
        return False
        
    def filter_items(self, intelligence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter a list of intelligence items to only include European or missionary relevant items
        
        Args:
            intelligence_items: List of intelligence item dictionaries
            
        Returns:
            List[Dict[str, Any]]: Filtered list of intelligence items
        """
        filtered_items = []
        
        for item in intelligence_items:
            if self.is_relevant(item):
                filtered_items.append(item)
                
        logger.info(f"Filtered {len(intelligence_items)} items to {len(filtered_items)} Europe/missionary relevant items")
        return filtered_items
        
    def filter_database_results(self, results: List[tuple]) -> List[tuple]:
        """
        Filter database query results to only include European or missionary relevant items
        
        Args:
            results: List of database result tuples
            
        Returns:
            List[tuple]: Filtered list of database results
        """
        filtered_results = []
        
        for result in results:
            # Convert tuple to dict for filtering
            item = {
                'id': result[0] if len(result) > 0 else None,
                'title': result[1] if len(result) > 1 else '',
                'content': result[2] if len(result) > 2 else '',
                'source': result[3] if len(result) > 3 else '',
                'region': result[4] if len(result) > 4 else '',
                'country': result[5] if len(result) > 5 else '',
                'missionary_relevance': result[6] if len(result) > 6 else 0
            }
            
            if self.is_relevant(item):
                filtered_results.append(result)
                
        logger.info(f"Filtered {len(results)} database results to {len(filtered_results)} Europe/missionary relevant results")
        return filtered_results

def filter_intelligence(data: Union[Dict[str, Any], List[Dict[str, Any]], List[tuple]]) -> Union[Dict[str, Any], List[Dict[str, Any]], List[tuple]]:
    """
    Filter intelligence data to only include items relevant to Europe or European missionaries
    
    Args:
        data: Intelligence data to filter (dict, list of dicts, or database results)
        
    Returns:
        Filtered intelligence data
    """
    filter_instance = EuropeFilter()
    
    # Handle different input types
    if isinstance(data, dict):
        # Single intelligence item
        return data if filter_instance.is_relevant(data) else None
    elif isinstance(data, list):
        if not data:
            return []
            
        # Check if it's a list of dicts or database results
        if isinstance(data[0], dict):
            return filter_instance.filter_items(data)
        else:
            return filter_instance.filter_database_results(data)
    else:
        logger.warning(f"Unsupported data type for filtering: {type(data)}")
        return data

# Command-line interface for testing
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Filter intelligence data for European or missionary relevance')
    parser.add_argument('--file', help='JSON file containing intelligence items to filter')
    args = parser.parse_args()
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                data = json.load(f)
                
            filtered_data = filter_intelligence(data)
            print(json.dumps(filtered_data, indent=2))
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("No input file specified. Use --file to specify a JSON file.", file=sys.stderr)
        sys.exit(1)
