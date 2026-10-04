import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_health_live(client):
    """Test that the liveness endpoint returns a successful response."""
    response = client.get('/api/v1/health/live')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'alive'
    assert data['service'] == 'canteen-backend'

def test_health_ready(client):
    """Test that the readiness endpoint returns a successful response."""
    response = client.get('/api/v1/health/ready')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['dependencies']['database'] == 'healthy'
