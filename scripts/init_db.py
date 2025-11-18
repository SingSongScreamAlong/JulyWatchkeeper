#!/usr/bin/env python3
"""
Initialize WATCHKEEPER Database

This script:
1. Creates database tables using Alembic migrations
2. Creates an admin user
3. Initializes Elasticsearch indices
4. Seeds sample data (optional)
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, engine
from app.models.user import User
from app.auth import get_password_hash
from app.tasks.search import initialize_indices
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(db, username="admin", email="admin@watchkeeper.org", password="Admin123!"):
    """Create initial admin user"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        logger.info(f"✓ Admin user '{username}' already exists")
        return existing_user
    
    # Create new admin user
    admin = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(password),
        is_active=True,
        is_admin=True
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    logger.info(f"✓ Created admin user: {username}")
    logger.info(f"  Email: {email}")
    logger.info(f"  Password: {password}")
    logger.info(f"  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
    
    return admin


def seed_sample_data(db):
    """Seed sample data for testing"""
    from app.models.intelligence import IntelligenceItem
    from app.models.personnel import Personnel
    from app.models.geofence import Geofence
    from datetime import datetime
    
    logger.info("Seeding sample data...")
    
    # Check if data already exists
    if db.query(IntelligenceItem).count() > 0:
        logger.info("✓ Sample data already exists, skipping")
        return
    
    # Add sample intelligence
    sample_intel = IntelligenceItem(
        title="Sample Intelligence Item",
        content="This is a sample intelligence item for testing purposes.",
        source="sample_source",
        category="security",
        region="Middle East",
        threat_level=5,
        missionary_relevance=7,
        created_at=datetime.utcnow()
    )
    db.add(sample_intel)
    
    # Add sample personnel
    sample_personnel = Personnel(
        name="John Doe",
        organization="Test Organization",
        region="Middle East",
        status="active",
        checkin_frequency=3600  # 1 hour
    )
    db.add(sample_personnel)
    
    db.commit()
    logger.info("✓ Sample data seeded")


def main():
    """Main initialization function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize WATCHKEEPER database")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--email", default="admin@watchkeeper.org", help="Admin email")
    parser.add_argument("--password", default="Admin123!", help="Admin password")
    parser.add_argument("--seed", action="store_true", help="Seed sample data")
    parser.add_argument("--init-search", action="store_true", help="Initialize Elasticsearch indices")
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("WATCHKEEPER Database Initialization")
    logger.info("=" * 60)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create admin user
        logger.info("\n1. Creating admin user...")
        create_admin_user(db, args.username, args.email, args.password)
        
        # Seed sample data if requested
        if args.seed:
            logger.info("\n2. Seeding sample data...")
            seed_sample_data(db)
        
        # Initialize Elasticsearch if requested
        if args.init_search:
            logger.info("\n3. Initializing Elasticsearch indices...")
            try:
                initialize_indices()
                logger.info("✓ Elasticsearch indices created")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize Elasticsearch: {e}")
                logger.warning("   You can initialize later with: python -c 'from app.tasks.search import initialize_indices; initialize_indices()'")
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Database initialization complete!")
        logger.info("=" * 60)
        logger.info(f"\nLogin credentials:")
        logger.info(f"  Username: {args.username}")
        logger.info(f"  Password: {args.password}")
        logger.info(f"\n⚠️  CHANGE THE DEFAULT PASSWORD IMMEDIATELY!")
        logger.info("\nNext steps:")
        logger.info("  1. Start the API: docker-compose up -d")
        logger.info("  2. Access API docs: http://localhost:8000/docs")
        logger.info("  3. Start frontend: cd frontend && npm run dev")
        logger.info("  4. Access dashboard: http://localhost:3000\n")
        
    except Exception as e:
        logger.error(f"❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
