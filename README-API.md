# WATCHKEEPER Backend API

This document provides instructions for setting up and running the WATCHKEEPER Backend API with authentication.

## Overview

The WATCHKEEPER Backend API is built with FastAPI and provides secure endpoints for managing intelligence items, tags, and verification information. All API endpoints are protected with JWT authentication.

## Features

- **Secure Authentication**: JWT-based authentication using OAuth2 password flow
- **Protected API Endpoints**: All endpoints require authentication
- **Comprehensive API**: Full CRUD operations for intelligence items, tags, and verification info
- **Database Integration**: PostgreSQL database with SQLAlchemy ORM
- **Docker Support**: Easy deployment with Docker and docker-compose

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL
- Docker and docker-compose (optional)

### Environment Setup

1. **Clone the repository**

2. **Set up environment variables**

   Create a `.env` file in the project root with the following variables:

   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost/watchkeeper
   SECRET_KEY=your_secret_key_here
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   API_HOST=0.0.0.0
   API_PORT=8000
   API_DEBUG=true
   LOG_LEVEL=INFO
   ```

3. **Set up a virtual environment**

   ```bash
   # Run the setup script
   ./scripts/setup_venv.sh
   
   # Or manually set up the environment
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Initialize the database**

   ```bash
   # Using the script
   python scripts/init_database.py --sample-data
   
   # Or manually
   psql -U postgres -c "CREATE DATABASE watchkeeper;"
   psql -U postgres -d watchkeeper -f init_db.sql
   ```

### Running the API

1. **Run with Python**

   ```bash
   # Activate the virtual environment
   source .venv/bin/activate
   
   # Run the server
   python run.py
   ```

2. **Run with Docker**

   ```bash
   docker-compose up -d api
   ```

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Authentication

### Getting a Token

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=adminpassword"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

```bash
curl -X GET "http://localhost:8000/api/v1/intelligence/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Testing

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_auth.py
```

## Default Users

The API comes with two default users for testing:

1. **Admin User**
   - Username: `admin`
   - Password: `adminpassword`

2. **Analyst User**
   - Username: `analyst`
   - Password: `analystpassword`

## Next Steps

- Develop frontend application
- Integrate alert/notification system
- Connect to external APIs for automated intelligence gathering
