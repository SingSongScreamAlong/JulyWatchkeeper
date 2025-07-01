#!/usr/bin/env python

import os
import sys
import argparse
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine
from app.models import IntelligenceItem, Tag, VerificationInfo
from app.utils.db_init import init_db

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_argparse():
    parser = argparse.ArgumentParser(description='Initialize the WATCHKEEPER database')
    parser.add_argument('--force', action='store_true', help='Force recreation of tables (drops existing tables)')
    parser.add_argument('--sample-data', action='store_true', help='Load sample data after initialization')
    parser.add_argument('--sql-file', type=str, default='init_db.sql', help='SQL file to use for initialization')
    return parser.parse_args()

def create_tables():
    """Create database tables from SQLAlchemy models"""
    try:
        logger.info("Creating database tables from SQLAlchemy models...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        return False

def drop_tables():
    """Drop all database tables"""
    try:
        logger.info("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error dropping tables: {e}")
        return False

def load_sql_file(sql_file):
    """Load SQL from file and execute"""
    try:
        # Find the SQL file path
        sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), sql_file)
        
        if not os.path.exists(sql_path):
            logger.error(f"SQL file not found: {sql_path}")
            return False
        
        logger.info(f"Loading SQL from {sql_path}")
        with open(sql_path, 'r') as f:
            sql = f.read()
        
        # Execute SQL
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        
        logger.info("SQL executed successfully")
        return True
    except Exception as e:
        logger.error(f"Error loading SQL file: {e}")
        return False

def main():
    # Parse command line arguments
    args = setup_argparse()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize database connection
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(f"Database connection successful: {result.fetchone()}")
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {e}")
        return False
    
    # Drop tables if force flag is set
    if args.force:
        if not drop_tables():
            return False
    
    # Create tables
    if not create_tables():
        return False
    
    # Load sample data if requested
    if args.sample_data:
        if not load_sql_file(args.sql_file):
            return False
    
    logger.info("Database initialization complete")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
