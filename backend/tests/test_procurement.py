import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.category import Category
from app.models.stall import Stall
from app.models.product import Product
from app.models.inventory import Inventory
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
        manager = User(email='manager@example.com', password_hash='hash', name='Manager', role='CANTEEN_MANAGER')
        cat = Category(name='Drinks')
        stall1 = Stall(name='Drink Stall')
        db.session.add_all([manager, cat, stall1])
        db.session.commit()
        
        prod1 = Product(name='Coke', price=20.0, category_id=cat.id, stall_id=stall1.id)
        db.session.add(prod1)
        db.session.commit()
        
        inv1 = Inventory(product_id=prod1.id, quantity=10, low_stock_threshold=20)
        db.session.add(inv1)
        db.session.commit()

        token = generate_token(manager)
        return {
            'token': token,
            'product_id': prod1.id
        }

def test_supplier_crud(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    
    # 1. Create Supplier
    res = client.post('/api/v1/suppliers', json={"name": "ABC Foods"}, headers=headers)
    assert res.status_code == 201
    supplier_id = res.get_json()['data']['id']
    
    # 2. Add product to supplier
    res = client.post(f'/api/v1/suppliers/{supplier_id}/products', json={
        "product_id": seed_data['product_id'],
        "purchase_price": 15.0
    }, headers=headers)
    assert res.status_code == 201
    
    return supplier_id

def test_procurement_workflow(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["token"]}'}
    supplier_id = test_supplier_crud(client, seed_data)
    
    # 1. Create Purchase Request
    res = client.post('/api/v1/procurement/requests', json={
        "items": [
            {"product_id": seed_data['product_id'], "quantity": 100}
        ]
    }, headers=headers)
    assert res.status_code == 201
    req_id = res.get_json()['data']['id']
    
    # 2. Approve Request (auto-converts to PO)
    res = client.post(f'/api/v1/procurement/requests/{req_id}/approve', headers=headers)
    assert res.status_code == 200
    
    # Get PO from DB to find ID (since API returns po_number)
    from app.models.procurement import PurchaseOrder
    with client.application.app_context():
        po = PurchaseOrder.query.first()
        po_id = po.id
        
    # 3. Send and Confirm PO
    res = client.post(f'/api/v1/procurement/orders/{po_id}/send', headers=headers)
    assert res.status_code == 200
    
    res = client.post(f'/api/v1/procurement/orders/{po_id}/confirm', json={}, headers=headers)
    assert res.status_code == 200
    
    # 4. Receive Goods
    with client.application.app_context():
        from app.models.procurement import PurchaseOrder
        po = PurchaseOrder.query.get(po_id)
        po_item_id = po.items[0].id
        
    res = client.post('/api/v1/procurement/receipts', json={
        "po_id": po_id,
        "items": [
            {
                "po_item_id": po_item_id,
                "received_quantity": 100,
                "rejected_quantity": 0,
                "damaged_quantity": 5
            }
        ]
    }, headers=headers)
    
    assert res.status_code == 201
    
    # 5. Check Inventory update (Started at 10, added 95 accepted)
    with client.application.app_context():
        from app.models.inventory import Inventory
        inv = Inventory.query.filter_by(product_id=seed_data['product_id']).first()
        assert inv.quantity == 105
