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
        stall1 = Stall(name='Drink Stall')
        db.session.add_all([manager, cat, stall1])
        db.session.commit()
        
        prod1 = Product(name='Coke', price=20.0, category_id=cat.id, stall_id=stall1.id)
        prod2 = Product(name='Pepsi', price=20.0, category_id=cat.id, stall_id=stall1.id)
        db.session.add_all([prod1, prod2])
        db.session.commit()
        
        inv1 = Inventory(product_id=prod1.id, quantity=0, low_stock_threshold=5) # Out of stock
        inv2 = Inventory(product_id=prod2.id, quantity=3, low_stock_threshold=5) # Low stock
        db.session.add_all([inv1, inv2])
        db.session.commit()

        # Create orders today
        o1 = Order(order_number='O1', subtotal=40.0, total=40.0, status='PLACED')
        o1_item = OrderItem(order_id=1, product_id=prod1.id, product_name_snapshot='Coke', quantity=2, unit_price=20.0, subtotal=40.0)
        
        o2 = Order(order_number='O2', subtotal=20.0, total=20.0, status='FULFILLED')
        o2_item = OrderItem(order_id=2, product_id=prod2.id, product_name_snapshot='Pepsi', quantity=1, unit_price=20.0, subtotal=20.0)
        
        db.session.add_all([o1, o2])
        db.session.flush()
        
        o1_item.order_id = o1.id
        o2_item.order_id = o2.id
        db.session.add_all([o1_item, o2_item])
        db.session.commit()

        token = generate_token(manager)
        return {
            'token': token
        }

def test_analytics_overview(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    res = client.get('/api/v1/analytics/overview', headers=headers)
    assert res.status_code == 200
    data = res.get_json()['data']
    
    assert data['orders'] == 2
    assert data['revenue'] == 60.0
    assert data['items_sold'] == 3
    assert data['active_orders'] == 1 # O1 is PLACED
    assert data['out_of_stock'] == 1
    assert data['low_stock'] == 1
    assert data['average_order_value'] == 30.0

def test_analytics_sales(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    res = client.get('/api/v1/analytics/sales', headers=headers)
    assert res.status_code == 200
    data = res.get_json()['data']
    assert len(data['trend']) > 0
    assert data['peak_hour']['orders'] >= 1
    assert data['peak_hour']['revenue'] > 0

def test_analytics_products(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    res = client.get('/api/v1/analytics/products', headers=headers)
    assert res.status_code == 200
    data = res.get_json()['data']
    
    top_products = data['top_products']
    assert len(top_products) == 2
    assert top_products[0]['name'] == 'Coke'
    assert top_products[0]['units_sold'] == 2

def test_analytics_stalls(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    res = client.get('/api/v1/analytics/stalls', headers=headers)
    assert res.status_code == 200
    data = res.get_json()['data']
    
    assert len(data) == 0 # Wait, in seed_data, did we create fulfillments? No. 
    # The stall analytics relies on Fulfillment records. If they are missing, it returns 0.

def test_analytics_fulfillment(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    res = client.get('/api/v1/analytics/fulfillment', headers=headers)
    assert res.status_code == 200
    data = res.get_json()['data']
    assert 'average_fulfillment_seconds' in data
    assert 'completed_count' in data
    assert 'delayed_orders_count' in data

def test_analytics_inventory(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    res = client.get('/api/v1/analytics/inventory', headers=headers)
    assert res.status_code == 200
    data = res.get_json()['data']
    assert 'total_waste' in data
    assert 'stockout_risks' in data
    assert 'restock_recommendations' in data

