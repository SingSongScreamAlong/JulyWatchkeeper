#!/usr/bin/env python3
"""
API Key Management Utility for Watchkeeper
This script helps manage API keys for various intelligence sources
"""

import os
import json
import argparse
import logging
import getpass
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv, set_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.api_keys')

# Default paths
DEFAULT_ENV_FILE = '.env'
DEFAULT_CONFIG_DIR = 'config'
DEFAULT_COMBINED_SOURCES = 'config/combined_sources.json'

class ApiKeyManager:
    """Manages API keys for Watchkeeper intelligence sources"""
    
    def __init__(self, env_file: str = DEFAULT_ENV_FILE, sources_file: str = DEFAULT_COMBINED_SOURCES):
        """Initialize the API key manager"""
        self.env_file = env_file
        self.sources_file = sources_file
        self.required_keys = set()
        
        # Create .env file if it doesn't exist
        env_path = Path(self.env_file)
        if not env_path.exists():
            env_path.touch()
            logger.info(f"Created empty environment file: {self.env_file}")
            
        # Load environment variables
        load_dotenv(self.env_file)
        
    def scan_sources(self) -> List[str]:
        """Scan source configurations for required API keys"""
        required_keys = set()
        
        try:
            # Check if sources file exists
            if not os.path.exists(self.sources_file):
                logger.warning(f"Sources file not found: {self.sources_file}")
                return list(required_keys)
                
            # Load sources file
            with open(self.sources_file, 'r') as f:
                data = json.load(f)
                
            # Handle flat sources array
            if 'sources' in data:
                sources = data['sources']
                self._extract_keys_from_sources(sources, required_keys)
            
            # Handle category-based organization
            else:
                for category, category_sources in data.items():
                    if isinstance(category_sources, list):
                        self._extract_keys_from_sources(category_sources, required_keys)
                        
            self.required_keys = required_keys
            return sorted(list(required_keys))
            
        except Exception as e:
            logger.error(f"Error scanning sources: {e}")
            return list(required_keys)
    
    def _extract_keys_from_sources(self, sources: List[Dict], required_keys: set):
        """Extract required API keys from a list of sources"""
        for source in sources:
            # Check for environment variables in params
            params = source.get('params', {})
            for param_value in params.values():
                if isinstance(param_value, str) and param_value.startswith('$'):
                    key_name = param_value[1:]  # Remove $ prefix
                    required_keys.add(key_name)
            
            # Check for explicit env_vars list
            env_vars = source.get('env_vars', [])
            for env_var in env_vars:
                required_keys.add(env_var)
    
    def check_keys(self) -> Dict[str, bool]:
        """Check if required API keys are set in environment"""
        if not self.required_keys:
            self.scan_sources()
            
        key_status = {}
        for key in self.required_keys:
            value = os.environ.get(key)
            key_status[key] = bool(value)
            
        return key_status
    
    def set_key(self, key_name: str, key_value: Optional[str] = None) -> bool:
        """Set an API key in the environment file"""
        if key_value is None:
            # Prompt for key value if not provided
            key_value = getpass.getpass(f"Enter value for {key_name}: ")
            
        try:
            # Set the key in the .env file
            set_key(self.env_file, key_name, key_value)
            logger.info(f"Set API key: {key_name}")
            
            # Reload environment variables
            load_dotenv(self.env_file, override=True)
            return True
            
        except Exception as e:
            logger.error(f"Error setting API key {key_name}: {e}")
            return False
    
    def list_keys(self) -> Dict[str, str]:
        """List all API keys and their status"""
        if not self.required_keys:
            self.scan_sources()
            
        key_info = {}
        for key in self.required_keys:
            value = os.environ.get(key)
            if value:
                # Mask the actual value for security
                masked_value = value[:3] + '*' * (len(value) - 6) + value[-3:] if len(value) > 6 else '******'
                status = f"SET ({masked_value})"
            else:
                status = "NOT SET"
                
            key_info[key] = status
            
        return key_info
    
    def get_missing_keys(self) -> List[str]:
        """Get a list of required keys that are not set"""
        key_status = self.check_keys()
        return [key for key, is_set in key_status.items() if not is_set]

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Watchkeeper API Key Management Utility')
    parser.add_argument('--env', default=DEFAULT_ENV_FILE, help='Path to environment file')
    parser.add_argument('--sources', default=DEFAULT_COMBINED_SOURCES, help='Path to sources configuration')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List required API keys and their status')
    
    # Set command
    set_parser = subparsers.add_parser('set', help='Set an API key')
    set_parser.add_argument('key', help='Name of the API key to set')
    set_parser.add_argument('--value', help='Value for the API key (if not provided, will prompt securely)')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Check if all required API keys are set')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Interactive setup of all missing API keys')
    
    args = parser.parse_args()
    
    # Initialize API key manager
    manager = ApiKeyManager(args.env, args.sources)
    
    # Execute command
    if args.command == 'list':
        key_info = manager.list_keys()
        if key_info:
            print("\nRequired API Keys:")
            for key, status in key_info.items():
                print(f"  {key}: {status}")
        else:
            print("No API keys required in the current configuration")
            
    elif args.command == 'set':
        success = manager.set_key(args.key, args.value)
        if success:
            print(f"Successfully set API key: {args.key}")
        else:
            print(f"Failed to set API key: {args.key}")
            
    elif args.command == 'check':
        key_status = manager.check_keys()
        all_set = all(key_status.values())
        
        if all_set:
            print("All required API keys are set")
        else:
            missing_keys = [key for key, is_set in key_status.items() if not is_set]
            print(f"Missing API keys: {', '.join(missing_keys)}")
            print("\nUse the following commands to set them:")
            for key in missing_keys:
                print(f"  python manage_api_keys.py set {key}")
                
    elif args.command == 'setup':
        missing_keys = manager.get_missing_keys()
        
        if not missing_keys:
            print("All required API keys are already set")
        else:
            print(f"Setting up {len(missing_keys)} missing API keys...")
            for key in missing_keys:
                manager.set_key(key)
                
            print("\nAPI key setup complete")
    else:
        # Default action: scan and show status
        manager.scan_sources()
        key_info = manager.list_keys()
        
        if key_info:
            print("\nRequired API Keys:")
            for key, status in key_info.items():
                print(f"  {key}: {status}")
                
            missing_keys = manager.get_missing_keys()
            if missing_keys:
                print(f"\n{len(missing_keys)} keys need to be configured")
                print("Run 'python manage_api_keys.py setup' for interactive setup")
        else:
            print("No API keys required in the current configuration")

if __name__ == "__main__":
    main()
