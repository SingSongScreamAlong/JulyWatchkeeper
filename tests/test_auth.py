import sys
import os
import pytest
from fastapi.testclient import TestClient
import json
from datetime import timedelta

# Add the parent directory to the path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.auth import create_access_token, users_db

# Create test client
client = TestClient(app)

# Test authentication endpoints
def test_login_success():
    response = client.post(
        "/token",
        data={"username": "admin", "password": "adminpassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_login_invalid_credentials():
    response = client.post(
        "/token",
        data={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()

def test_get_current_user():
    # Create a valid token
    access_token = create_access_token(
        data={"sub": "admin"}, expires_delta=timedelta(minutes=30)
    )
    
    # Test with valid token
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "admin"

def test_get_current_user_invalid_token():
    # Test with invalid token
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()

# Test protected endpoints
def test_protected_endpoints():
    # Create a valid token
    access_token = create_access_token(
        data={"sub": "admin"}, expires_delta=timedelta(minutes=30)
    )
    
    # Test intelligence endpoint with valid token
    response = client.get(
        "/api/v1/intelligence/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    
    # Test tags endpoint with valid token
    response = client.get(
        "/api/v1/tags/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    
    # Test verification endpoint with valid token
    response = client.get(
        "/api/v1/verification/",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

def test_protected_endpoints_no_auth():
    # Test intelligence endpoint without token
    response = client.get("/api/v1/intelligence/")
    assert response.status_code == 401
    
    # Test tags endpoint without token
    response = client.get("/api/v1/tags/")
    assert response.status_code == 401
    
    # Test verification endpoint without token
    response = client.get("/api/v1/verification/")
    assert response.status_code == 401

if __name__ == "__main__":
    pytest.main(['-xvs', __file__])
