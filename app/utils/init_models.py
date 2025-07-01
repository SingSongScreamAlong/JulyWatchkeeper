import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the models
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import Base, engine
from app.models import IntelligenceItem, Tag, VerificationInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_models():
    """
    Initialize the database tables based on SQLAlchemy models.
    """
    try:
        # Create tables
        logger.info("Creating database tables from SQLAlchemy models...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database initialization error: {e}")
        return False

if __name__ == "__main__":
    # Initialize models when script is run directly
    success = init_models()
    if success:
        print("Database models initialized successfully")
    else:
        print("Failed to initialize database models")
        sys.exit(1)
