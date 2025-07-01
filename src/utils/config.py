"""
Configuration management for WATCHKEEPER

This module handles loading and validating configuration from various sources:
1. Default configuration
2. Configuration file (config.yaml)
3. Environment variables
4. Command line arguments
"""

import os
import yaml
import argparse
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    "collectors": {
        "news": {
            "enabled": True,
            "sources": ["bbc", "reuters", "dw"],
            "rate_limit": 60,  # requests per minute
            "languages": ["en", "fr", "de", "es", "it"]
        },
        "social_media": {
            "enabled": False,
            "sources": ["twitter", "reddit"],
            "rate_limit": 30
        },
        "government": {
            "enabled": False,
            "sources": ["france", "germany", "uk"],
            "rate_limit": 10
        }
    },
    "processors": {
        "ai": {
            "model": "llama3.1:8b",
            "host": "localhost",
            "batch_size": 8,
            "max_tokens": 1024
        },
        "nlp": {
            "languages": ["en", "fr", "de"],
            "entity_extraction": True,
            "sentiment_analysis": True
        },
        "geographic": {
            "enabled": True,
            "coordinate_extraction": True
        }
    },
    "api": {
        "host": "0.0.0.0",
        "port": 8000,
        "workers": 4,
        "cors_origins": ["*"]
    },
    "database": {
        "type": "sqlite",  # sqlite, postgresql
        "path": "data/watchkeeper.db",
        "host": "",
        "port": 0,
        "username": "",
        "password": "",
        "database": ""
    },
    "logging": {
        "level": "INFO",
        "file_rotation": True,
        "max_size_mb": 10,
        "backup_count": 5
    }
}

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from multiple sources and merge them
    
    Args:
        config_path: Path to the configuration file (optional)
        
    Returns:
        Dict[str, Any]: Merged configuration
    """
    # Start with default configuration
    config = DEFAULT_CONFIG.copy()
    
    # Load configuration from file if provided
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    _deep_update(config, file_config)
        except Exception as e:
            print(f"Error loading configuration from {config_path}: {e}")
    
    # Override with environment variables
    _update_from_env(config)
    
    # Override with command line arguments
    _update_from_args(config)
    
    return config


def get_config(config_path: str = None) -> Dict[str, Any]:
    """
    Alias for load_config to maintain compatibility with existing code
    
    Args:
        config_path: Path to the configuration file (optional)
        
    Returns:
        Dict[str, Any]: Merged configuration
    """
    return load_config(config_path)

def _deep_update(target: Dict, source: Dict) -> None:
    """
    Deep update target dict with source
    For each key in source, if the key exists in target and both values are dicts,
    recursively update the nested dict. Otherwise, update the target key with the source value.
    
    Args:
        target: Target dictionary to update
        source: Source dictionary with new values
    """
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _deep_update(target[key], value)
        else:
            target[key] = value

def _update_from_env(config: Dict) -> None:
    """
    Update configuration from environment variables
    Environment variables should be prefixed with WATCHKEEPER_
    For nested keys, use double underscore as separator
    
    Example:
        WATCHKEEPER_API__PORT=9000 will set config["api"]["port"] = 9000
    
    Args:
        config: Configuration dictionary to update
    """
    prefix = "WATCHKEEPER_"
    for key, value in os.environ.items():
        if key.startswith(prefix):
            key_path = key[len(prefix):].lower().split("__")
            
            # Navigate to the correct nested dictionary
            current = config
            for part in key_path[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value, converting to appropriate type
            if key_path[-1] in current:
                orig_value = current[key_path[-1]]
                if isinstance(orig_value, bool):
                    current[key_path[-1]] = value.lower() in ('true', 'yes', '1')
                elif isinstance(orig_value, int):
                    current[key_path[-1]] = int(value)
                elif isinstance(orig_value, float):
                    current[key_path[-1]] = float(value)
                elif isinstance(orig_value, list):
                    current[key_path[-1]] = value.split(',')
                else:
                    current[key_path[-1]] = value

def _update_from_args(config: Dict) -> None:
    """
    Update configuration from command line arguments
    
    Args:
        config: Configuration dictionary to update
    """
    parser = argparse.ArgumentParser(description='WATCHKEEPER Intelligence Platform')
    
    # Add command line arguments
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--api-port', type=int, help='API server port')
    parser.add_argument('--ai-model', help='AI model name')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        help='Logging level')
    
    args = parser.parse_args()
    
    # Update configuration with command line arguments
    if args.api_port:
        config['api']['port'] = args.api_port
    
    if args.ai_model:
        config['processors']['ai']['model'] = args.ai_model
    
    if args.log_level:
        config['logging']['level'] = args.log_level
