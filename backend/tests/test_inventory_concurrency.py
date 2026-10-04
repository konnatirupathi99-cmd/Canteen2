import pytest
from app import create_app
from app.extensions import db
from app.models.category import Category
from app.models.stall import Stall
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.user import User
from app.auth.middleware import generate_token
import threading

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def seed_data(app):
    with app.app_context():
        cashier = User(email='cashier@example.com', password_hash='hash', name='Cashier', role='CASHIER')
        cat = Category(name='Burgers')
        stall1 = Stall(name='Burger Stall')
        db.session.add_all([cashier, cat, stall1])
        db.session.commit()
        
        prod1 = Product(name='Chicken Burger', price=100.0, category_id=cat.id, stall_id=stall1.id)
        db.session.add(prod1)
        db.session.commit()
        
        # Initial stock = 1
        inv1 = Inventory(product_id=prod1.id, quantity=1, low_stock_threshold=5)
        db.session.add(inv1)
        db.session.commit()
        
        token = generate_token(cashier)
        return {
            'token': token,
            'prod1_id': prod1.id
        }

def test_inventory_race_condition(app, seed_data):
    """
    Test 10 concurrent requests trying to buy the same item with stock = 1.
    Expected: Exactly 1 succeeds, 9 fail with OUT_OF_STOCK / INSUFFICIENT_STOCK.
    """
    results = []
    
    def worker():
        client = app.test_client()
        headers = {'Authorization': f'Bearer {seed_data["token"]}'}
        data = {
            "items": [
                {"product_id": seed_data["prod1_id"], "quantity": 1}
            ]
        }
        res = client.post('/api/v1/orders/checkout', json=data, headers=headers)
        results.append(res.status_code)

    threads = []
    for i in range(10):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()

    successes = results.count(200)
    failures = results.count(400)
    
    assert successes == 1, f"Expected exactly 1 success, got {successes}"
    assert failures == 9, f"Expected exactly 9 failures, got {failures}"
    
    with app.app_context():
        inv = Inventory.query.filter_by(product_id=seed_data["prod1_id"]).first()
        assert inv.quantity == 0, f"Stock should be 0, got {inv.quantity}"
