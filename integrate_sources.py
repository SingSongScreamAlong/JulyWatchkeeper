#!/usr/bin/env python3
"""
Integrate Intelligence Sources
This script integrates all intelligence sources into the Watchkeeper system
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.integrate_sources')

class SourceIntegrator:
    """Integrates intelligence sources into the Watchkeeper system"""
    
    def __init__(self, config_dir: str = 'config', combined_file: str = 'config/combined_sources.json'):
        """Initialize the source integrator"""
        self.config_dir = config_dir
        self.combined_file = combined_file
        
    def merge_sources(self) -> bool:
        """Merge all source configuration files"""
        logger.info("Merging intelligence source configurations...")
        
        # Find all source configuration files
        source_files = []
        for file in os.listdir(self.config_dir):
            if file.endswith('_sources.json') and file != 'combined_sources.json':
                source_files.append(os.path.join(self.config_dir, file))
                
        if not source_files:
            logger.error("No source configuration files found")
            return False
            
        # Run the merge_sources.py script
        try:
            cmd = [sys.executable, 'merge_sources.py', '--sources'] + source_files + ['--output', self.combined_file]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to merge sources: {result.stderr}")
                return False
                
            logger.info(f"Successfully merged {len(source_files)} source files")
            return True
            
        except Exception as e:
            logger.error(f"Error merging sources: {e}")
            return False
    
    def check_api_keys(self) -> Dict[str, bool]:
        """Check if required API keys are set"""
        logger.info("Checking required API keys...")
        
        try:
            cmd = [sys.executable, 'manage_api_keys.py', 'check']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse the output to determine key status
            key_status = {}
            if "All required API keys are set" in result.stdout:
                logger.info("All required API keys are set")
            elif "Missing API keys:" in result.stdout:
                logger.warning("Some API keys are missing")
                # Extract missing keys from output
                for line in result.stdout.split('\n'):
                    if line.startswith("Missing API keys:"):
                        missing_keys = line.replace("Missing API keys:", "").strip().split(', ')
                        for key in missing_keys:
                            key_status[key] = False
            
            return key_status
            
        except Exception as e:
            logger.error(f"Error checking API keys: {e}")
            return {}
    
    def validate_sources(self) -> Dict[str, List[str]]:
        """Validate all sources in the combined configuration"""
        logger.info("Validating intelligence sources...")
        
        try:
            if not os.path.exists(self.combined_file):
                logger.error(f"Combined sources file not found: {self.combined_file}")
                return {"errors": ["Combined sources file not found"]}
                
            with open(self.combined_file, 'r') as f:
                data = json.load(f)
                
            sources = data.get('sources', [])
            if not sources:
                logger.error("No sources found in combined configuration")
                return {"errors": ["No sources found in combined configuration"]}
                
            # Validate each source
            validation_results = {"valid": [], "invalid": []}
            required_fields = ['name', 'url', 'type']
            
            for source in sources:
                name = source.get('name', 'Unknown')
                
                # Check required fields
                missing_fields = [field for field in required_fields if field not in source]
                if missing_fields:
                    logger.warning(f"Source '{name}' is missing required fields: {', '.join(missing_fields)}")
                    validation_results["invalid"].append(f"{name} (missing: {', '.join(missing_fields)})")
                    continue
                    
                # Check source type
                source_type = source.get('type')
                if source_type not in ['rss', 'api', 'web']:
                    logger.warning(f"Source '{name}' has invalid type: {source_type}")
                    validation_results["invalid"].append(f"{name} (invalid type: {source_type})")
                    continue
                    
                # Additional validation based on source type
                if source_type == 'api' and 'params' not in source:
                    logger.warning(f"API source '{name}' is missing 'params' field")
                    validation_results["invalid"].append(f"{name} (missing params for API)")
                    continue
                    
                if source_type == 'web' and 'selectors' not in source:
                    logger.warning(f"Web scraping source '{name}' is missing 'selectors' field")
                    validation_results["invalid"].append(f"{name} (missing selectors for web scraping)")
                    continue
                    
                # Source is valid
                validation_results["valid"].append(name)
                
            logger.info(f"Validated {len(sources)} sources: {len(validation_results['valid'])} valid, {len(validation_results['invalid'])} invalid")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating sources: {e}")
            return {"errors": [str(e)]}
    
    def update_guardian_config(self, config_file: str = 'config/guardian_config.json') -> bool:
        """Update the Guardian system configuration to use the combined sources"""
        logger.info("Updating Guardian system configuration...")
        
        try:
            # Create or update guardian config
            config = {}
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            
            # Update sources configuration
            config['sources_file'] = self.combined_file
            config['enable_all_sources'] = True
            
            # Add other default settings if not present
            if 'collection_interval' not in config:
                config['collection_interval'] = 15  # minutes
            
            if 'database' not in config:
                config['database'] = {
                    'path': 'data/intelligence.db',
                    'backup_dir': 'data/backups'
                }
                
            if 'logging' not in config:
                config['logging'] = {
                    'level': 'INFO',
                    'file': 'logs/watchkeeper.log',
                    'max_size': 10485760,  # 10MB
                    'backup_count': 5
                }
                
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # Write updated config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            logger.info(f"Updated Guardian configuration: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating Guardian configuration: {e}")
            return False
    
    def run_integration(self) -> Dict[str, Any]:
        """Run the complete integration process"""
        results = {}
        
        # Step 1: Merge sources
        merge_success = self.merge_sources()
        results['merge_sources'] = merge_success
        
        if not merge_success:
            return results
            
        # Step 2: Validate sources
        validation_results = self.validate_sources()
        results['validation'] = validation_results
        
        # Step 3: Check API keys
        key_status = self.check_api_keys()
        results['api_keys'] = key_status
        
        # Step 4: Update Guardian configuration
        config_updated = self.update_guardian_config()
        results['guardian_config'] = config_updated
        
        return results

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Integrate Intelligence Sources into Watchkeeper')
    parser.add_argument('--config-dir', default='config', help='Directory containing source configurations')
    parser.add_argument('--combined-file', default='config/combined_sources.json', help='Path for combined sources')
    parser.add_argument('--guardian-config', default='config/guardian_config.json', help='Path for Guardian config')
    
    args = parser.parse_args()
    
    # Run integration
    integrator = SourceIntegrator(args.config_dir, args.combined_file)
    results = integrator.run_integration()
    
    # Print summary
    print("\nIntegration Summary:")
    
    if results.get('merge_sources', False):
        print("✅ Sources merged successfully")
    else:
        print("❌ Failed to merge sources")
        
    validation = results.get('validation', {})
    valid_count = len(validation.get('valid', []))
    invalid_count = len(validation.get('invalid', []))
    print(f"✅ Sources validated: {valid_count} valid, {invalid_count} invalid")
    
    if invalid_count > 0:
        print("\nInvalid Sources:")
        for source in validation.get('invalid', []):
            print(f"  - {source}")
            
    api_keys = results.get('api_keys', {})
    if api_keys:
        print("\nMissing API Keys:")
        for key in api_keys:
            print(f"  - {key}")
        print("\nRun 'python manage_api_keys.py setup' to configure missing API keys")
        
    if results.get('guardian_config', False):
        print("✅ Guardian configuration updated")
    else:
        print("❌ Failed to update Guardian configuration")
        
    print("\nIntegration complete. Run 'python guardian.py' to start the Watchkeeper system.")

if __name__ == "__main__":
    main()
