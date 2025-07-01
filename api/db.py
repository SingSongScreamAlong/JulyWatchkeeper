"""
WatchKeeper API - Database Module
Provides database connection functionality
"""
import logging
import sqlite3
from pathlib import Path
from fastapi import HTTPException, status
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path('logs/api.log'), mode='a')
    ]
)
logger = logging.getLogger("watchkeeper.api.db")

# Load configuration
def load_config():
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

config = load_config()

# Database connection
def get_db_connection():
    # First try to find the database in the data directory (where guardian.py writes to)
    db_path = Path("data/intelligence.db").resolve()
    if not db_path.exists():
        # Try to find the database in the project root directory (one level up from api/)
        db_path = Path("../intelligence.db").resolve()
        if not db_path.exists():
            # Fallback to the current directory
            db_path = Path(config.get("database_path", "intelligence.db"))
            if not db_path.exists():
                logger.error(f"Database file not found: {db_path}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Intelligence database not found"
                )
        
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )
