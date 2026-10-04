import pytest
from app.models import IntelligenceSignal, Recommendation, RecommendationAudit, Product, Category, Stall, Inventory
from app.services.intelligence_service import IntelligenceService
from app.extensions import db
from app import create_app

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_setup(app):
    with app.app_context():
        # Clean db
        db.drop_all()
        db.create_all()
        
        stall = Stall(name="Test Stall")
        db.session.add(stall)
        db.session.commit()
        
        cat = Category(name="Test Category")
        db.session.add(cat)
        db.session.commit()
        
        prod = Product(name="Test Product", stall_id=stall.id, category_id=cat.id, price=10.0)
        db.session.add(prod)
        db.session.commit()
        
        inv = Inventory(product_id=prod.id, quantity=5, low_stock_threshold=10)
        db.session.add(inv)
        db.session.commit()
        
        yield prod

def test_intelligence_snapshot(app, test_setup):
    with app.app_context():
        snapshot = IntelligenceService.get_real_time_snapshot()
        assert snapshot is not None
        assert snapshot['active_orders'] == 0
        assert snapshot['critical_stock_items'] == 1 # 5 <= 10

def test_create_recommendation(app, test_setup):
    with app.app_context():
        rec = IntelligenceService.create_recommendation(
            type="REORDER",
            reason="Low stock",
            suggested_action={"action": "reorder", "qty": 50},
            product_id=test_setup.id
        )
        assert rec is not None
        assert rec.type == "REORDER"
        assert rec.get_action()["qty"] == 50
        
def test_evaluate_endpoint(client, test_setup):
    # Need admin/manager token for testing
    from app.models import User
    from werkzeug.security import generate_password_hash
    from app.auth.middleware import generate_token
    
    with client.application.app_context():
        admin = User(email="admin_intel@test.com", name="Admin", password_hash=generate_password_hash("pass"), role="ADMIN")
        db.session.add(admin)
        db.session.commit()
        token = generate_token(admin)
        
    res = client.post('/api/v1/intelligence/evaluate', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    # Should not crash, numbers of signals depend on logic

def test_simulate_scenario(client, test_setup):
    from app.models import User
    from werkzeug.security import generate_password_hash
    from app.auth.middleware import generate_token
    
    with client.application.app_context():
        admin = User(email="admin_intel2@test.com", name="Admin2", password_hash=generate_password_hash("pass"), role="ADMIN")
        db.session.add(admin)
        db.session.commit()
        token = generate_token(admin)
        
    # Test DEMAND_SPIKE
    payload = {
        "scenario_type": "DEMAND_SPIKE",
        "params": {
            "product_id": test_setup.id,
            "multiplier": 3.0
        }
    }
    res = client.post('/api/v1/intelligence/simulate', headers={'Authorization': f'Bearer {token}'}, json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['result']['scenario'] == "DEMAND_SPIKE"
