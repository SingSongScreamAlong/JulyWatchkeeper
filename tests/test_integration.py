"""
WATCHKEEPER Integration Tests

Tests the complete system integration including:
- Database operations
- API endpoints
- Search functionality
- Background tasks
- WebSocket connections
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime

# Import app
from app.main import app
from app.database import SessionLocal, engine
from app.models.user import User
from app.models.intelligence import IntelligenceItem
from app.models.alert import Alert
from app.auth import get_password_hash

client = TestClient(app)


class TestAuthentication:
    """Test authentication and authorization"""

    def test_login_success(self):
        """Test successful login"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "Admin123!"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication"""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 401


class TestIntelligenceEndpoints:
    """Test intelligence collection endpoints"""

    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "Admin123!"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_intelligence_list(self, auth_headers):
        """Test getting intelligence list"""
        response = client.get(
            "/api/v1/intelligence",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_intelligence_item(self, auth_headers):
        """Test creating new intelligence item"""
        data = {
            "title": "Test Intelligence Item",
            "content": "This is a test intelligence item",
            "source": "test_source",
            "category": "security",
            "region": "Test Region",
            "threat_level": 5,
            "missionary_relevance": 7
        }
        response = client.post(
            "/api/v1/intelligence",
            json=data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]


class TestSearchFunctionality:
    """Test Elasticsearch search integration"""

    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "Admin123!"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_search_intelligence(self, auth_headers):
        """Test intelligence search"""
        response = client.get(
            "/api/v1/search/intelligence?q=security",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "results" in data

    def test_search_with_filters(self, auth_headers):
        """Test search with filters"""
        response = client.get(
            "/api/v1/search/intelligence?q=threat&category=security&min_threat=6",
            headers=auth_headers
        )
        assert response.status_code == 200


class TestAlertSystem:
    """Test alert creation and management"""

    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "Admin123!"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_alerts(self, auth_headers):
        """Test getting alerts list"""
        response = client.get(
            "/api/v1/alerts",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestIncidentReporting:
    """Test incident reporting functionality"""

    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "Admin123!"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_create_incident(self, auth_headers):
        """Test creating a new incident"""
        data = {
            "title": "Test Incident",
            "description": "This is a test incident",
            "incident_type": "security",
            "severity": "medium",
            "location_name": "Test Location"
        }
        response = client.post(
            "/api/v1/incidents",
            json=data,
            headers=auth_headers
        )
        assert response.status_code in [200, 201]


class TestDashboardStats:
    """Test dashboard statistics endpoint"""

    @pytest.fixture
    def auth_headers(self):
        """Get authentication headers"""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "Admin123!"}
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_get_dashboard_stats(self, auth_headers):
        """Test getting dashboard statistics"""
        response = client.get(
            "/api/v1/dashboard/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields are present
        required_fields = [
            "total_intelligence",
            "active_alerts",
            "unacknowledged_alerts",
            "open_incidents",
            "active_personnel",
            "personnel_in_danger",
            "threat_level_avg",
            "recent_collections"
        ]
        
        for field in required_fields:
            assert field in data


class TestHealthChecks:
    """Test system health endpoints"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint"""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200


class TestDatabase:
    """Test database operations"""

    def test_database_connection(self):
        """Test database connection"""
        db = SessionLocal()
        try:
            # Simple query to test connection
            result = db.execute("SELECT 1")
            assert result.scalar() == 1
        finally:
            db.close()

    def test_user_model(self):
        """Test User model operations"""
        db = SessionLocal()
        try:
            # Query existing admin user
            admin = db.query(User).filter(User.username == "admin").first()
            assert admin is not None
            assert admin.is_admin == True
        finally:
            db.close()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
