#!/usr/bin/env python3
"""
Merge Intelligence Sources
This script merges multiple intelligence source configuration files into a single combined file
"""

import json
import logging
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.merge_sources')

def merge_sources(source_files: List[str], output_file: str) -> bool:
    """
    Merge multiple source configuration files into a single file
    
    Args:
        source_files: List of source configuration file paths
        output_file: Path to output the merged configuration
        
    Returns:
        bool: True if successful, False otherwise
    """
    all_sources = []
    source_names = set()
    
    # Process each source file
    for source_file in source_files:
        if not os.path.exists(source_file):
            logger.warning(f"Source file not found: {source_file}")
            continue
            
        try:
            with open(source_file, 'r') as f:
                data = json.load(f)
            
            # Handle different file structures
            sources = []
            
            # Case 1: Flat sources array
            if 'sources' in data:
                sources = data['sources']
                logger.info(f"Found {len(sources)} sources in {source_file} (flat structure)")
            
            # Case 2: Category-based organization
            else:
                # Look for category arrays like emergency_alerts, news_media, etc.
                for category, category_sources in data.items():
                    if isinstance(category_sources, list):
                        # Add category as a field to each source
                        for source in category_sources:
                            if isinstance(source, dict):
                                source['source_category'] = category
                        
                        sources.extend(category_sources)
                        
                logger.info(f"Found {len(sources)} sources across categories in {source_file}")
            
            # Check for duplicate sources
            for source in sources:
                name = source.get('name')
                if name in source_names:
                    logger.warning(f"Duplicate source '{name}' found, keeping the first occurrence")
                    continue
                    
                source_names.add(name)
                all_sources.append(source)
                
        except Exception as e:
            logger.error(f"Error processing {source_file}: {e}")
            return False
    
    if not all_sources:
        logger.error("No sources found in any of the provided files")
        return False
        
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Write merged sources to output file
    try:
        with open(output_file, 'w') as f:
            json.dump({"sources": all_sources}, f, indent=4)
            
        logger.info(f"Successfully merged {len(all_sources)} sources into {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error writing merged sources to {output_file}: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Merge Intelligence Source Configuration Files')
    parser.add_argument('--sources', nargs='+', default=['config/sources.json', 'config/new_sources.json', 'config/open_sources.json'], 
                        help='Source configuration files to merge')
    parser.add_argument('--output', default='config/combined_sources.json',
                        help='Output file for merged configuration')
    args = parser.parse_args()
    
    success = merge_sources(args.sources, args.output)
    if success:
        print(f"Successfully merged sources into {args.output}")
    else:
        print("Failed to merge sources. Check logs for details.")

if __name__ == "__main__":
    main()
