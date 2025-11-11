"""
Database Initialization Script for WATCHKEEPER

This script creates all database tables and seeds initial data.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from src.core.database import engine, AsyncSessionLocal
from src.models import *  # Import all models
from src.crud.crud_user import crud_user
from src.crud.crud_role import crud_role, crud_permission
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")

    from src.core.database import Base

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created successfully")


async def main():
    """Main initialization function."""
    logger.info("=== WATCHKEEPER Database Initialization ===")

    try:
        # Create tables
        await create_tables()

        logger.info("=== Database initialization completed successfully ===")

    except Exception as e:
        logger.error(f"Error during initialization: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
