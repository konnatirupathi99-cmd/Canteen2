import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.stall import Stall
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.auth.middleware import generate_token
from datetime import datetime, timedelta

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def seed_data(app):
    with app.app_context():
        manager = User(email='manager@example.com', password_hash='hash', name='Manager', role='CANTEEN_MANAGER')
        cat = Category(name='Drinks')
        stall = Stall(name='Drink Stall')
        db.session.add_all([manager, cat, stall])
        db.session.commit()
        
        prod = Product(name='Coke', price=20.0, category_id=cat.id, stall_id=stall.id)
        db.session.add(prod)
        db.session.commit()
        
        inv = Inventory(product_id=prod.id, quantity=50, low_stock_threshold=20)
        db.session.add(inv)
        db.session.commit()
        
        # Add historical orders
        for i in range(1, 8):
            dt = datetime.utcnow() - timedelta(days=i)
            o = Order(order_number=f"ORD-{i}", subtotal=100.0, total=100.0, status='FULFILLED', created_at=dt)
            db.session.add(o)
            db.session.flush()
            oi = OrderItem(order_id=o.id, product_id=prod.id, product_name_snapshot='Coke', quantity=10, unit_price=20.0, subtotal=200.0)
            db.session.add(oi)
            
        db.session.commit()

        token = generate_token(manager)
        return {
            'token': token,
            'product_id': prod.id,
            'stall_id': stall.id
        }

def test_generate_forecast(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    
    # 1. Generate Forecast
    res = client.post('/api/v1/predictive/forecasts/generate', json={
        "product_id": seed_data['product_id']
    }, headers=headers)
    assert res.status_code == 200
    data = res.get_json()['data']
    assert len(data) == 1
    assert data[0]['predicted_quantity'] == 10 # 7 days of 10 items/day = avg 10
    
    # 2. Get Dashboard
    res = client.get('/api/v1/predictive/dashboard', headers=headers)
    assert res.status_code == 200

def test_waste_recording(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    
    # Record Waste
    res = client.post('/api/v1/predictive/waste', json={
        "product_id": seed_data['product_id'],
        "stall_id": seed_data['stall_id'],
        "quantity": 5,
        "reason": "Expired"
    }, headers=headers)
    
    assert res.status_code == 201
    
    # Verify Inventory deducted
    with client.application.app_context():
        inv = Inventory.query.filter_by(product_id=seed_data['product_id']).first()
        assert inv.quantity == 45 # Started at 50

def test_preparation_plan(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    
    res = client.post('/api/v1/predictive/preparation-plans', json={
        "product_id": seed_data['product_id'],
        "recommended_quantity": 100,
        "final_quantity": 110
    }, headers=headers)
    assert res.status_code == 200
    
    res = client.get('/api/v1/predictive/preparation-plans', headers=headers)
    assert res.status_code == 200
    assert len(res.get_json()['data']) == 1

def test_forecast_override(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    
    # Generate
    client.post('/api/v1/predictive/forecasts/generate', json={
        "product_id": seed_data['product_id']
    }, headers=headers)
    
    from app.models.predictive import Forecast
    with client.application.app_context():
        f = Forecast.query.first()
        f_id = f.id
        
    res = client.post(f'/api/v1/predictive/forecasts/{f_id}/override', json={
        "new_quantity": 25,
        "reason": "Special event"
    }, headers=headers)
    
    assert res.status_code == 200
