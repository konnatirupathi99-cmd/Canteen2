import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Institution, Campus, Canteen, OrganizationMembership
from app.models.stall import Stall
from app.models.product import GlobalProduct, Product
from app.models.inventory import Inventory
from app.auth.middleware import generate_token
from app.auth.scope import has_scope_permission
from datetime import datetime

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
        # Setup Hierarchy
        inst = Institution(name="Global Uni")
        db.session.add(inst)
        db.session.commit()
        
        campus1 = Campus(institution_id=inst.id, name="North Campus")
        campus2 = Campus(institution_id=inst.id, name="South Campus")
        db.session.add_all([campus1, campus2])
        db.session.commit()
        
        cant1 = Canteen(campus_id=campus1.id, name="North Canteen")
        cant2 = Canteen(campus_id=campus2.id, name="South Canteen")
        db.session.add_all([cant1, cant2])
        db.session.commit()
        
        stall1 = Stall(canteen_id=cant1.id, name="North Snacks")
        stall2 = Stall(canteen_id=cant2.id, name="South Drinks")
        db.session.add_all([stall1, stall2])
        db.session.commit()
        
        # Setup Users
        sys_admin = User(email="sys@example.com", password_hash="hash", name="Sys Admin", role="SYSTEM_ADMIN")
        canteen_mgr = User(email="mgr@example.com", password_hash="hash", name="Mgr", role="CANTEEN_MANAGER")
        db.session.add_all([sys_admin, canteen_mgr])
        db.session.commit()
        
        # Add scoping
        mem1 = OrganizationMembership(user_id=canteen_mgr.id, canteen_id=cant1.id, role="CANTEEN_MANAGER")
        db.session.add(mem1)
        db.session.commit()

        # Global Product
        gp = GlobalProduct(name="Coke", default_price=20.0)
        db.session.add(gp)
        from app.models.category import Category
        cat = Category(name="Beverage")
        db.session.add(cat)
        db.session.commit()

        # Local Products
        p1 = Product(global_product_id=gp.id, category_id=cat.id, stall_id=stall1.id, name="Coke North", price=20.0)
        p2 = Product(global_product_id=gp.id, category_id=cat.id, stall_id=stall2.id, name="Coke South", price=22.0)
        db.session.add_all([p1, p2])
        db.session.commit()
        
        # Inventory
        inv1 = Inventory(product_id=p1.id, quantity=100, low_stock_threshold=20)
        inv2 = Inventory(product_id=p2.id, quantity=10, low_stock_threshold=20)
        db.session.add_all([inv1, inv2])
        db.session.commit()

        return {
            'sys_admin_token': generate_token(sys_admin),
            'canteen_mgr_token': generate_token(canteen_mgr),
            'canteen1_id': cant1.id,
            'canteen2_id': cant2.id,
            'prod1_id': p1.id,
            'prod2_id': p2.id,
            'sys_admin_id': sys_admin.id
        }

def test_scope_resolution(app, seed_data):
    with app.app_context():
        mgr = User.query.get(2) # canteen_mgr
        
        # Should have access to cant1
        assert has_scope_permission(mgr, ['CANTEEN_MANAGER'], canteen_id=seed_data['canteen1_id']) == True
        # Should not have access to cant2
        assert has_scope_permission(mgr, ['CANTEEN_MANAGER'], canteen_id=seed_data['canteen2_id']) == False

def test_central_dashboard_isolation(client, seed_data):
    headers_mgr = {'Authorization': f'Bearer {seed_data["canteen_mgr_token"]}'}
    headers_admin = {'Authorization': f'Bearer {seed_data["sys_admin_token"]}'}
    
    # Manager trying to access Cant2 should fail
    res = client.get(f'/api/v1/central/dashboard?canteen_id={seed_data["canteen2_id"]}', headers=headers_mgr)
    assert res.status_code == 403
    
    # Manager trying to access Cant1 should succeed
    res = client.get(f'/api/v1/central/dashboard?canteen_id={seed_data["canteen1_id"]}', headers=headers_mgr)
    assert res.status_code == 200

def test_inventory_transfer(client, seed_data):
    headers = {'Authorization': f'Bearer {seed_data["sys_admin_token"]}'}
    
    # Request transfer 20 items from cant1 (100 in stock) to cant2 (10 in stock)
    res = client.post('/api/v1/central/transfers', json={
        "source_canteen_id": seed_data["canteen1_id"],
        "destination_canteen_id": seed_data["canteen2_id"],
        "product_id": seed_data["prod1_id"],
        "quantity": 20
    }, headers=headers)
    
    assert res.status_code == 200
    t_id = res.get_json()['data']['id']
    
    # Approve
    res = client.post(f'/api/v1/central/transfers/{t_id}/approve', headers=headers)
    assert res.status_code == 200
    
    # Dispatch
    res = client.post(f'/api/v1/central/transfers/{t_id}/dispatch', headers=headers)
    assert res.status_code == 200
    
    # Check inv1 deducted
    with client.application.app_context():
        inv1 = Inventory.query.filter_by(product_id=seed_data["prod1_id"]).first()
        assert inv1.quantity == 80
        
    # Receive
    res = client.post(f'/api/v1/central/transfers/{t_id}/receive', headers=headers)
    assert res.status_code == 200
    
    # Check inv2 added
    with client.application.app_context():
        inv2 = Inventory.query.filter_by(product_id=seed_data["prod2_id"]).first()
        assert inv2.quantity == 30
