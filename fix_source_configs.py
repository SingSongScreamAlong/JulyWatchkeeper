#!/usr/bin/env python3
"""
Fix Source Configurations
This script fixes invalid source configurations by adding required parameters
"""

import os
import json
import logging
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.fix_sources')

# Source fixes - adding required parameters for each invalid source
SOURCE_FIXES = {
    "OSAC": {
        "params": {
            "format": "json",
            "limit": 100
        }
    },
    "GDELT Project": {
        "params": {
            "format": "json",
            "mode": "artlist",
            "maxrecords": 100,
            "sort": "DateDesc"
        }
    },
    "ACLED": {
        "params": {
            "api_key": "$ACLED_API_KEY",
            "event_date": "2023-01-01|2023-12-31",
            "event_date_where": "BETWEEN",
            "format": "json"
        }
    },
    "ReliefWeb API": {
        "params": {
            "appname": "watchkeeper",
            "preset": "latest",
            "limit": 50,
            "format": "json"
        }
    },
    "Global Incident Map": {
        "selectors": {
            "item": ".incident-item",
            "title": ".incident-title",
            "description": ".incident-description",
            "date": ".incident-date",
            "location": ".incident-location"
        }
    },
    "IMB Piracy Reporting Centre": {
        "selectors": {
            "item": ".piracy-report",
            "title": ".report-title",
            "description": ".report-details",
            "date": ".report-date",
            "location": ".report-location"
        }
    },
    "UK FCDO Travel Advice": {
        "params": {
            "format": "json",
            "limit": 100
        }
    },
    "Reddit Europe": {
        "params": {
            "limit": 25,
            "sort": "hot"
        }
    },
    "Reddit World News": {
        "params": {
            "limit": 25,
            "sort": "hot"
        }
    }
}

def fix_combined_sources(file_path: str = 'config/combined_sources.json') -> bool:
    """Fix the combined sources configuration file"""
    logger.info(f"Fixing source configurations in {file_path}")
    
    try:
        # Load the combined sources file
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        sources = data.get('sources', [])
        if not sources:
            logger.error("No sources found in the configuration file")
            return False
            
        # Track fixed sources
        fixed_sources = []
        
        # Fix each source
        for source in sources:
            name = source.get('name')
            if name in SOURCE_FIXES:
                # Apply fixes
                for key, value in SOURCE_FIXES[name].items():
                    source[key] = value
                fixed_sources.append(name)
                
        # Write the updated configuration
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            
        logger.info(f"Fixed {len(fixed_sources)} sources: {', '.join(fixed_sources)}")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing sources: {e}")
        return False

def fix_original_sources() -> bool:
    """Fix the original source configuration files"""
    source_files = [
        'config/sources.json',
        'config/new_sources.json',
        'config/open_sources.json'
    ]
    
    success = True
    for file_path in source_files:
        if not os.path.exists(file_path):
            logger.warning(f"Source file not found: {file_path}")
            continue
            
        try:
            # Load the source file
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Check if it's a flat sources array or category-based
            if 'sources' in data:
                # Flat sources array
                sources = data['sources']
                fixed = fix_sources_list(sources)
                if fixed:
                    # Write the updated configuration
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=4)
                    logger.info(f"Fixed sources in {file_path}")
            else:
                # Category-based organization
                fixed = False
                for category, category_sources in data.items():
                    if isinstance(category_sources, list):
                        if fix_sources_list(category_sources):
                            fixed = True
                
                if fixed:
                    # Write the updated configuration
                    with open(file_path, 'w') as f:
                        json.dump(data, f, indent=4)
                    logger.info(f"Fixed sources in {file_path}")
                    
        except Exception as e:
            logger.error(f"Error fixing sources in {file_path}: {e}")
            success = False
            
    return success

def fix_sources_list(sources: List[Dict[str, Any]]) -> bool:
    """Fix a list of sources"""
    fixed = False
    for source in sources:
        name = source.get('name')
        if name in SOURCE_FIXES:
            # Apply fixes
            for key, value in SOURCE_FIXES[name].items():
                source[key] = value
            fixed = True
            
    return fixed

def main():
    """Main entry point"""
    # Fix the combined sources file
    combined_fixed = fix_combined_sources()
    
    # Fix the original source files
    originals_fixed = fix_original_sources()
    
    if combined_fixed or originals_fixed:
        print("Source configurations have been fixed successfully.")
        print("Run 'python integrate_sources.py' to re-validate the sources.")
    else:
        print("No changes were made to source configurations.")

if __name__ == "__main__":
    main()
