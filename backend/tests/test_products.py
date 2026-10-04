import pytest
from app import create_app
from app.extensions import db
from app.models.category import Category
from app.models.stall import Stall
from app.models.product import Product
from app.models.inventory import Inventory

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
        cat = Category(name='Burgers')
        stall = Stall(name='Burger Stall')
        db.session.add_all([cat, stall])
        db.session.commit()
        
        prod = Product(name='Chicken Burger', price=100.0, category_id=cat.id, stall_id=stall.id)
        db.session.add(prod)
        db.session.commit()
        
        inv = Inventory(product_id=prod.id, quantity=10, low_stock_threshold=2)
        db.session.add(inv)
        db.session.commit()

def test_get_products(client, seed_data):
    response = client.get('/api/v1/products')
    assert response.status_code == 200
    data = response.json['data']
    assert len(data) == 1
    assert data[0]['name'] == 'Chicken Burger'
    assert data[0]['price'] == 100.0
    assert data[0]['inventory']['quantity'] == 10
    assert data[0]['inventory']['state'] == 'IN_STOCK'

def test_get_categories(client, seed_data):
    response = client.get('/api/v1/categories')
    assert response.status_code == 200
    assert len(response.json['data']) == 1
    assert response.json['data'][0]['name'] == 'Burgers'
