import sys
import os
import pytest
from fastapi.testclient import TestClient
import json

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import get_db, Base, engine
from app.models import IntelligenceItem, Tag, VerificationInfo

# Create test client
client = TestClient(app)

# Test data
test_tag = {"name": "test_tag"}

test_intelligence = {
    "title": "Test Intelligence",
    "content": "This is a test intelligence item",
    "summary": "Test summary",
    "source": "Test Source",
    "source_id": 999,
    "raw_content": "Raw test content",
    "url": "https://example.com/test",
    "collection_date": "2025-07-01T12:00:00Z",
    "publication_date": "2025-07-01T10:00:00Z",
    "threat_level": 5.0,
    "missionary_relevance": 6.0,
    "region": "Test Region",
    "country": "Test Country",
    "location": "Test Location",
    "latitude": 0.0,
    "longitude": 0.0,
    "keywords": "test, api, intelligence",
    "sentiment": 0.0,
    "confidence": 0.9,
    "tags": ["test_tag"]
}

test_verification = {
    "source_verified": True,
    "url_verified": True,
    "timestamp": "2025-07-01T12:30:00Z",
    "verification_method": "test_method",
    "verification_agent": "test_agent"
}

# Setup and teardown for tests
@pytest.fixture(scope="module")
def setup_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)

# Test root endpoint
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to WATCHKEEPER API"}

# Test health check endpoint
def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

# Test tag endpoints
def test_tag_crud(setup_database):
    # Create tag
    response = client.post("/api/v1/tags/", json=test_tag)
    assert response.status_code == 201
    created_tag = response.json()
    assert created_tag["name"] == test_tag["name"]
    tag_id = created_tag["id"]
    
    # Get tag
    response = client.get(f"/api/v1/tags/{tag_id}")
    assert response.status_code == 200
    assert response.json()["name"] == test_tag["name"]
    
    # Update tag
    updated_tag = {"name": "updated_test_tag"}
    response = client.put(f"/api/v1/tags/{tag_id}", json=updated_tag)
    assert response.status_code == 200
    assert response.json()["name"] == updated_tag["name"]
    
    # Get all tags
    response = client.get("/api/v1/tags/")
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # Delete tag (we'll do this after testing intelligence items)
    # response = client.delete(f"/api/v1/tags/{tag_id}")
    # assert response.status_code == 204

# Test intelligence endpoints
def test_intelligence_crud(setup_database):
    # Create intelligence item
    response = client.post("/api/v1/intelligence/", json=test_intelligence)
    assert response.status_code == 201
    created_item = response.json()
    assert created_item["title"] == test_intelligence["title"]
    item_id = created_item["id"]
    
    # Get intelligence item
    response = client.get(f"/api/v1/intelligence/{item_id}")
    assert response.status_code == 200
    assert response.json()["title"] == test_intelligence["title"]
    
    # Update intelligence item
    updated_item = test_intelligence.copy()
    updated_item["title"] = "Updated Test Intelligence"
    response = client.put(f"/api/v1/intelligence/{item_id}", json=updated_item)
    assert response.status_code == 200
    assert response.json()["title"] == updated_item["title"]
    
    # Get all intelligence items
    response = client.get("/api/v1/intelligence/")
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # Get intelligence stats
    response = client.get("/api/v1/intelligence/stats/overview")
    assert response.status_code == 200
    assert "total_items" in response.json()
    
    # Test filtering
    response = client.get(f"/api/v1/intelligence/?region={test_intelligence['region']}")
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # Delete intelligence item (we'll do this after testing verification)
    # response = client.delete(f"/api/v1/intelligence/{item_id}")
    # assert response.status_code == 204
    
    return item_id

# Test verification endpoints
def test_verification_crud(setup_database):
    # First create an intelligence item to verify
    item_id = test_intelligence_crud(setup_database)
    
    # Create verification info
    response = client.post(f"/api/v1/verification/{item_id}/verify", json=test_verification)
    assert response.status_code == 200
    created_verification = response.json()
    assert created_verification["intelligence_id"] == item_id
    
    # Get verification info
    response = client.get(f"/api/v1/verification/{item_id}")
    assert response.status_code == 200
    assert response.json()["verification_agent"] == test_verification["verification_agent"]
    
    # Update verification info
    updated_verification = test_verification.copy()
    updated_verification["verification_agent"] = "updated_test_agent"
    response = client.put(f"/api/v1/verification/{item_id}", json=updated_verification)
    assert response.status_code == 200
    assert response.json()["verification_agent"] == updated_verification["verification_agent"]
    
    # Get all verification info
    response = client.get("/api/v1/verification/")
    assert response.status_code == 200
    assert len(response.json()) > 0
    
    # Delete verification info
    response = client.delete(f"/api/v1/verification/{item_id}")
    assert response.status_code == 204
    
    # Delete the intelligence item
    response = client.delete(f"/api/v1/intelligence/{item_id}")
    assert response.status_code == 204
    
    # Find the tag ID and delete it
    response = client.get("/api/v1/tags/")
    tags = response.json()
    for tag in tags:
        if tag["name"] == "updated_test_tag":
            tag_id = tag["id"]
            response = client.delete(f"/api/v1/tags/{tag_id}")
            assert response.status_code == 204
            break

if __name__ == "__main__":
    pytest.main(['-xvs', __file__])
