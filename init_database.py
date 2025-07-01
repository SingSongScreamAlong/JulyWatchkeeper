#!/usr/bin/env python3
"""
Initialize the Watchkeeper Intelligence Database
This script creates the database tables and populates them with initial data
"""

import os
import sqlite3
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('watchkeeper.init_db')

def init_database(db_path: str = 'data/intelligence.db', force: bool = False):
    """Initialize the SQLite database with schema and sample data"""
    
    # Ensure data directory exists
    data_dir = os.path.dirname(db_path)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        logger.info(f"Created data directory: {data_dir}")
    
    # Check if database already exists
    if os.path.exists(db_path) and not force:
        logger.warning(f"Database already exists at {db_path}. Use --force to overwrite.")
        return False
    
    # Read SQL initialization script
    try:
        with open('init_db.sql', 'r') as f:
            sql_script = f.read()
    except Exception as e:
        logger.error(f"Error reading SQL script: {e}")
        return False
    
    # Execute SQL script
    try:
        conn = sqlite3.connect(db_path)
        conn.executescript(sql_script)
        conn.commit()
        logger.info(f"Successfully initialized database at {db_path}")
        
        # Verify tables were created
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info(f"Created tables: {', '.join([t[0] for t in tables])}")
        
        # Count sample data
        cursor.execute("SELECT COUNT(*) FROM intelligence_items;")
        count = cursor.fetchone()[0]
        logger.info(f"Inserted {count} sample intelligence items")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Initialize Watchkeeper Intelligence Database')
    parser.add_argument('--db', default='data/intelligence.db', help='Path to database file')
    parser.add_argument('--force', action='store_true', help='Force overwrite if database exists')
    args = parser.parse_args()
    
    success = init_database(args.db, args.force)
    if success:
        print("Database initialization complete!")
    else:
        print("Database initialization failed. Check logs for details.")

if __name__ == "__main__":
    main()
