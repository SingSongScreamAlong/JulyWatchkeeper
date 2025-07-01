#!/usr/bin/env python3
"""
WatchKeeper Database Initialization Script
Creates the necessary database tables for the WatchKeeper API
"""
import sqlite3
import os
import sys
import json
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("watchkeeper.db.init")

def load_config():
    """Load configuration from settings.json"""
    config_path = Path("../config/settings.json")
    if not config_path.exists():
        config_path = Path("config/settings.json")
        
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        return {}
        
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def initialize_database():
    """Initialize the database with required tables"""
    config = load_config()
    # Calculate the project root path (2 levels up from the script)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    db_path = project_root / "data" / "intelligence.db"
    
    # Make sure the directory exists
    db_dir = db_path.parent
    if not db_dir.exists():
        db_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing database at {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create sources table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            source_type TEXT NOT NULL,
            reliability_score REAL NOT NULL,
            language TEXT NOT NULL,
            country TEXT,
            last_checked TEXT,
            is_active INTEGER NOT NULL,
            collection_frequency INTEGER NOT NULL,
            rate_limit INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create intelligence_items table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS intelligence_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT,
            source TEXT NOT NULL,
            url TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            threat_level REAL NOT NULL,
            missionary_relevance REAL NOT NULL,
            region TEXT,
            country TEXT,
            tags TEXT,
            latitude REAL,
            longitude REAL
        )
        ''')
        
        # Insert sample data if the table is empty
        cursor.execute("SELECT COUNT(*) FROM intelligence_items")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("Adding sample intelligence items")
            sample_data = [
                {
                    "title": "Civil Unrest in Eastland Capital",
                    "content": "Reports of growing civil unrest in the capital city of Eastland. Protests have turned violent in several districts.",
                    "summary": "Violent protests in Eastland Capital",
                    "source": "Global News Network",
                    "url": "https://gnn.com/eastland-unrest",
                    "timestamp": datetime.now().isoformat(),
                    "threat_level": 8.5,
                    "missionary_relevance": 7.0,
                    "region": "Eastern Europe",
                    "country": "Eastland",
                    "tags": "civil unrest,violence,protests",
                    "latitude": 47.4979,
                    "longitude": 19.0402
                },
                {
                    "title": "Flooding in Southern Westland",
                    "content": "Severe flooding has affected multiple communities in Southern Westland. Evacuation orders in place.",
                    "summary": "Flooding emergency in Southern Westland",
                    "source": "Weather Alert Service",
                    "url": "https://weather-alert.org/westland-floods",
                    "timestamp": datetime.now().isoformat(),
                    "threat_level": 7.2,
                    "missionary_relevance": 6.5,
                    "region": "Western Africa",
                    "country": "Westland",
                    "tags": "natural disaster,flooding,evacuation",
                    "latitude": 6.5244,
                    "longitude": -9.4258
                },
                {
                    "title": "Political Tensions in Northland",
                    "content": "Political tensions are rising in Northland following disputed election results. International observers express concern.",
                    "summary": "Political crisis brewing in Northland",
                    "source": "International Affairs Journal",
                    "url": "https://iaj.org/northland-election-dispute",
                    "timestamp": datetime.now().isoformat(),
                    "threat_level": 6.8,
                    "missionary_relevance": 5.5,
                    "region": "Northern Asia",
                    "country": "Northland",
                    "tags": "political,election,dispute",
                    "latitude": 61.5240,
                    "longitude": 105.3188
                },
                {
                    "title": "Disease Outbreak in Southland Province",
                    "content": "Health authorities report a serious outbreak of an unidentified respiratory disease in Southland Province.",
                    "summary": "Disease outbreak in Southland",
                    "source": "Global Health Monitor",
                    "url": "https://ghm.org/southland-outbreak",
                    "timestamp": datetime.now().isoformat(),
                    "threat_level": 9.0,
                    "missionary_relevance": 8.5,
                    "region": "Southern Africa",
                    "country": "Southland",
                    "tags": "health,disease,outbreak",
                    "latitude": -30.5595,
                    "longitude": 22.9375
                },
                {
                    "title": "Terrorist Activity in Central Midland",
                    "content": "Security forces have uncovered evidence of increased terrorist activity in Central Midland. Heightened alert status.",
                    "summary": "Terrorist threat in Central Midland",
                    "source": "Security Intelligence Network",
                    "url": "https://sin.org/midland-terror-alert",
                    "timestamp": datetime.now().isoformat(),
                    "threat_level": 9.5,
                    "missionary_relevance": 9.0,
                    "region": "Middle East",
                    "country": "Midland",
                    "tags": "terrorism,security,alert",
                    "latitude": 23.8859,
                    "longitude": 45.0792
                }
            ]
            
            for item in sample_data:
                cursor.execute('''
                INSERT INTO intelligence_items 
                (title, content, summary, source, url, timestamp, threat_level, missionary_relevance, 
                region, country, tags, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item["title"], 
                    item["content"], 
                    item["summary"], 
                    item["source"], 
                    item["url"], 
                    item["timestamp"], 
                    item["threat_level"], 
                    item["missionary_relevance"], 
                    item["region"], 
                    item["country"], 
                    item["tags"],
                    item["latitude"],
                    item["longitude"]
                ))
        
        conn.commit()
        logger.info("Database initialization complete")
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    # Adjust working directory if needed
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    success = initialize_database()
    sys.exit(0 if success else 1)
