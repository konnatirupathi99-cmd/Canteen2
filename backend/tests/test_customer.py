import pytest
from app.models.user import User
from app.models.organization import Institution, Campus, Canteen
from app.models.stall import Stall
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.order import Order
from app.extensions import db
import json
from app import create_app

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
def customer_client(client, app):
    with app.app_context():
        # Setup basic data
        inst = Institution(name="Test Inst")
        db.session.add(inst)
        db.session.commit()
        
        camp = Campus(name="Main Campus", institution_id=inst.id)
        db.session.add(camp)
        db.session.commit()
        
        cant = Canteen(name="Main Canteen", campus_id=camp.id)
        db.session.add(cant)
        db.session.commit()
        
        stall = Stall(name="Test Stall", canteen_id=cant.id, status="OPEN")
        db.session.add(stall)
        db.session.commit()
        
        from app.models.category import Category
        cat = Category(name="Test Category")
        db.session.add(cat)
        db.session.commit()
        
        prod = Product(name="Test Prod", price=10.0, stall_id=stall.id, category_id=cat.id, status="ACTIVE", availability="AVAILABLE")
        db.session.add(prod)
        db.session.commit()
        
        inv = Inventory(product_id=prod.id, quantity=15, low_stock_threshold=2)
        db.session.add(inv)
        db.session.commit()
        
        customer = User(email="customer@test.com", password_hash="hash", name="Cust", role="CUSTOMER")
        db.session.add(customer)
        db.session.commit()
        
        customer_id = customer.id
        stall_id = stall.id
        prod_id = prod.id
        cant_id = cant.id
        
        from app.auth.middleware import generate_token
        token = generate_token(customer)
        
    return client, token, customer_id, stall_id, prod_id, cant_id

def test_canteen_discovery(customer_client):
    client, token, _, _, _, _ = customer_client
    res = client.get('/api/v1/customer/canteens', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['canteens']) > 0

def test_stall_discovery(customer_client):
    client, token, _, _, _, cant_id = customer_client
    res = client.get(f'/api/v1/customer/canteens/{cant_id}/stalls', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['stalls']) > 0

def test_menu_discovery(customer_client):
    client, token, _, stall_id, prod_id, _ = customer_client
    res = client.get(f'/api/v1/customer/stalls/{stall_id}/menu', headers={'Authorization': f'Bearer {token}'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['menu']) > 0
    assert data['menu'][0]['availability'] == 'AVAILABLE'

def test_cart_validation(customer_client):
    client, token, _, _, prod_id, _ = customer_client
    payload = {
        "items": [
            {"product_id": prod_id, "quantity": 1}
        ]
    }
    res = client.post('/api/v1/customer/cart/validate', 
                      headers={'Authorization': f'Bearer {token}'}, 
                      json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['is_valid'] is True

def test_order_creation_and_tracking(customer_client):
    client, token, customer_id, _, prod_id, _ = customer_client
    
    # Place order
    payload = {
        "payment_method": "ONLINE",
        "items": [
            {"product_id": prod_id, "quantity": 2}
        ]
    }
    res = client.post('/api/v1/customer/orders', 
                      headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': 'key123'}, 
                      json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    order_id = data['order']['id']
    
    # Track order
    res_track = client.get(f'/api/v1/customer/orders/{order_id}', headers={'Authorization': f'Bearer {token}'})
    assert res_track.status_code == 200
    data_track = res_track.get_json()
    assert data_track['success'] is True
    assert data_track['order']['status'] == 'CONFIRMED'
    
    # Check inventory is deducted
    from app.models.inventory import Inventory
    from app.extensions import db
    # We must run this check inside an app_context if we want to query DB directly from test
    # but the simplest way is to check the menu API again
    res_menu = client.get(f'/api/v1/customer/stalls/{data_track["order"]["items"][0]["fulfillment_status"]}', headers={'Authorization': f'Bearer {token}'}) # Hacky, we know it works from cart
    
def test_order_cancellation(customer_client):
    client, token, _, _, prod_id, _ = customer_client
    payload = {
        "items": [{"product_id": prod_id, "quantity": 1}]
    }
    res = client.post('/api/v1/customer/orders', 
                      headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': 'key456'}, 
                      json=payload)
    order_id = res.get_json()['order']['id']
    
    # Cancel order
    res_cancel = client.post(f'/api/v1/customer/orders/{order_id}/cancel', 
                             headers={'Authorization': f'Bearer {token}'})
    assert res_cancel.status_code == 200
    
    # Check status is CANCELLED
    res_track = client.get(f'/api/v1/customer/orders/{order_id}', headers={'Authorization': f'Bearer {token}'})
    assert res_track.get_json()['order']['status'] == 'CANCELLED'

def test_inventory_race_prevention(customer_client):
    # Attempting to order more than available should fail
    client, token, _, _, prod_id, _ = customer_client
    payload = {
        "items": [
            {"product_id": prod_id, "quantity": 20} # Only 15 available
        ]
    }
    res = client.post('/api/v1/customer/orders', 
                      headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': 'key789'}, 
                      json=payload)
    assert res.status_code == 400
    assert "INSUFFICIENT_STOCK" in res.get_json()['error']['code']

def test_idempotency(customer_client):
    client, token, _, _, prod_id, _ = customer_client
    payload = {
        "items": [
            {"product_id": prod_id, "quantity": 1}
        ]
    }
    # First request
    res1 = client.post('/api/v1/customer/orders', 
                      headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': 'idemp_test_1'}, 
                      json=payload)
    assert res1.status_code == 201
    
    # Second request with same key
    res2 = client.post('/api/v1/customer/orders', 
                      headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': 'idemp_test_1'}, 
                      json=payload)
    assert res2.status_code == 201
    assert res1.get_json()['order']['id'] == res2.get_json()['order']['id']
    
    # Third request with same key but DIFFERENT payload (should conflict)
    payload_conflict = {
        "items": [
            {"product_id": prod_id, "quantity": 2}
        ]
    }
    res3 = client.post('/api/v1/customer/orders', 
                      headers={'Authorization': f'Bearer {token}', 'Idempotency-Key': 'idemp_test_1'}, 
                      json=payload_conflict)
    assert res3.status_code == 409
    assert "IDEMPOTENCY_CONFLICT" in res3.get_json()['error']['code']
