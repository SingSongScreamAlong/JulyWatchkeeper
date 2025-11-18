#!/bin/bash
# WATCHKEEPER Quick Start Script
# This script sets up everything needed for first-time deployment

set -e

echo "=========================================="
echo "WATCHKEEPER v2.0 Quick Start"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    
    # Generate secret keys
    echo "Generating secure keys..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env with generated keys
    sed -i "s/your_super_secret_key_minimum_32_characters_change_this_immediately/$SECRET_KEY/" .env
    sed -i "s/your_encryption_master_key_minimum_32_characters_change_this/$ENCRYPTION_KEY/" .env
    
    echo -e "${GREEN}✓ Created .env file with generated keys${NC}"
    echo -e "${YELLOW}⚠️  Please review and update other settings in .env${NC}"
fi

echo ""
echo "Step 1: Starting Docker services..."
docker-compose up -d postgres redis elasticsearch

echo ""
echo "Waiting for services to be ready (30 seconds)..."
sleep 30

echo ""
echo "Step 2: Running database migrations..."
docker-compose run --rm api alembic upgrade head

echo ""
echo "Step 3: Initializing database..."
docker-compose run --rm api python scripts/init_db.py --seed --init-search

echo ""
echo "Step 4: Starting all services..."
docker-compose up -d

echo ""
echo "Step 5: Starting monitoring stack..."
docker-compose -f docker-compose.monitoring.yml up -d

echo ""
echo "=========================================="
echo -e "${GREEN}✓ WATCHKEEPER is ready!${NC}"
echo "=========================================="
echo ""
echo "Access your applications:"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Frontend Dashboard: http://localhost:3000"
echo "  • Grafana Monitoring: http://localhost:3001 (admin/admin123)"
echo ""
echo "Default login:"
echo "  Username: admin"
echo "  Password: Admin123!"
echo ""
echo -e "${YELLOW}⚠️  CHANGE THE DEFAULT PASSWORD IMMEDIATELY!${NC}"
echo ""
echo "To start the frontend:"
echo "  cd frontend"
echo "  npm install"
echo "  npm run dev"
echo ""
