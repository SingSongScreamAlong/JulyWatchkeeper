import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database connection string from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost/watchkeeper"
)

def init_db():
    """
    Initialize the database connection and create tables if they don't exist.
    """
    try:
        # Create SQLAlchemy engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"Database connection successful: {result.fetchone()}")
        
        # Read SQL initialization script
        sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "init_db.sql")
        
        if os.path.exists(sql_path):
            with open(sql_path, "r") as f:
                sql_script = f.read()
            
            # Execute SQL script
            with engine.connect() as connection:
                connection.execute(text(sql_script))
                connection.commit()
                logger.info("Database initialized successfully")
        else:
            logger.warning(f"SQL initialization file not found at {sql_path}")
        
        return engine
    except SQLAlchemyError as e:
        logger.error(f"Database initialization error: {e}")
        raise

if __name__ == "__main__":
    # Initialize database when script is run directly
    init_db()
