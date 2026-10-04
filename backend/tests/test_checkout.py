import pytest
from app import create_app
from app.extensions import db
from app.models.category import Category
from app.models.stall import Stall
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.user import User
from app.models.order import Order, Fulfillment
from app.auth.middleware import generate_token

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
        cashier = User(email='cashier@example.com', password_hash='hash', name='Cashier', role='CASHIER')
        cat = Category(name='Burgers')
        stall1 = Stall(name='Burger Stall')
        stall2 = Stall(name='Pizza Stall')
        db.session.add_all([cashier, cat, stall1, stall2])
        db.session.commit()
        
        prod1 = Product(name='Chicken Burger', price=100.0, category_id=cat.id, stall_id=stall1.id)
        prod2 = Product(name='Veg Pizza', price=200.0, category_id=cat.id, stall_id=stall2.id)
        db.session.add_all([prod1, prod2])
        db.session.commit()
        
        inv1 = Inventory(product_id=prod1.id, quantity=1, low_stock_threshold=0)
        inv2 = Inventory(product_id=prod2.id, quantity=10, low_stock_threshold=0)
        db.session.add_all([inv1, inv2])
        db.session.commit()
        
        token = generate_token(cashier)
        return {
            'token': token,
            'prod1_id': prod1.id,
            'prod2_id': prod2.id,
            'stall1_id': stall1.id,
            'stall2_id': stall2.id
        }

def test_successful_checkout(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    data = {
        "items": [
            {"product_id": seed_data["prod1_id"], "quantity": 1},
            {"product_id": seed_data["prod2_id"], "quantity": 1}
        ]
    }
    
    response = client.post('/api/v1/orders/checkout', json=data, headers=headers)
    if response.status_code != 200:
        print("ERROR RESPONSE:", response.json)
    assert response.status_code == 200
    assert response.json['success'] == True
    
    order_id = response.json['order']['id']
    
    # Check DB state
    from app.extensions import db
    with client.application.app_context():
        order = Order.query.get(order_id)
        assert order is not None
        assert order.total == 300.0
        assert len(order.fulfillments) == 2 # 2 different stalls
        
        inv1 = Inventory.query.filter_by(product_id=seed_data["prod1_id"]).first()
        assert inv1.quantity == 0

def test_insufficient_stock(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    # Prod1 has only 1 in stock
    data = {
        "items": [
            {"product_id": seed_data["prod1_id"], "quantity": 2},
        ]
    }
    
    response = client.post('/api/v1/orders/checkout', json=data, headers=headers)
    assert response.status_code == 400
    assert response.json['error']['code'] == 'INSUFFICIENT_STOCK'
