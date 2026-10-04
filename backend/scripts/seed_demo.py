import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import (
    User, Campus, Canteen, Stall, Category, GlobalProduct, Product, 
    Inventory, Supplier, SupplierProduct, Institution, OrganizationMembership
)
from werkzeug.security import generate_password_hash

def seed():
    app = create_app('development')
    with app.app_context():
        # Clear existing safe tables
        db.drop_all()
        db.create_all()

        print("Creating demo users...")
        users = [
            User(email="admin@canteen.com", name="System Admin", password_hash=generate_password_hash("demo123"), role="ADMIN"),
            User(email="manager@canteen.com", name="Canteen Manager", password_hash=generate_password_hash("demo123"), role="CANTEEN_MANAGER"),
            User(email="cashier@canteen.com", name="Cashier", password_hash=generate_password_hash("demo123"), role="CASHIER"),
            User(email="kitchen@canteen.com", name="Kitchen Staff", password_hash=generate_password_hash("demo123"), role="KITCHEN_STAFF"),
            User(email="customer@canteen.com", name="Customer", password_hash=generate_password_hash("demo123"), role="CUSTOMER")
        ]
        db.session.add_all(users)
        db.session.commit()

        print("Creating institution, campus, canteen, stall...")
        inst = Institution(name="Global University")
        db.session.add(inst)
        db.session.commit()

        campus = Campus(name="Main Campus", institution_id=inst.id)
        db.session.add(campus)
        db.session.commit()

        canteen = Canteen(name="Central Cafeteria", campus_id=campus.id)
        db.session.add(canteen)
        db.session.commit()

        # Add memberships
        db.session.add(OrganizationMembership(user_id=users[1].id, canteen_id=canteen.id, role="CANTEEN_MANAGER"))
        db.session.add(OrganizationMembership(user_id=users[2].id, canteen_id=canteen.id, role="CASHIER"))
        db.session.add(OrganizationMembership(user_id=users[3].id, canteen_id=canteen.id, role="KITCHEN_STAFF"))
        db.session.commit()

        stall1 = Stall(name="Burger Joint", canteen_id=canteen.id)
        stall2 = Stall(name="Healthy Salads", canteen_id=canteen.id)
        db.session.add_all([stall1, stall2])
        db.session.commit()

        print("Creating categories & products...")
        cat1 = Category(name="Fast Food", description="Burgers and fries")
        cat2 = Category(name="Healthy", description="Salads and bowls")
        db.session.add_all([cat1, cat2])
        db.session.commit()

        # Global products
        gp_burger = GlobalProduct(name="Classic Burger", default_price=5.99)
        gp_salad = GlobalProduct(name="Caesar Salad", default_price=7.50)
        gp_water = GlobalProduct(name="Bottled Water", default_price=1.00)
        db.session.add_all([gp_burger, gp_salad, gp_water])
        db.session.commit()

        # Local products
        p_burger = Product(name="Classic Burger", stall_id=stall1.id, category_id=cat1.id, price=5.99, global_product_id=gp_burger.id, preparation_time=5)
        p_salad = Product(name="Caesar Salad", stall_id=stall2.id, category_id=cat2.id, price=7.50, global_product_id=gp_salad.id, preparation_time=3)
        p_water = Product(name="Bottled Water", stall_id=stall1.id, category_id=cat1.id, price=1.00, global_product_id=gp_water.id, preparation_time=0)
        db.session.add_all([p_burger, p_salad, p_water])
        db.session.commit()

        print("Initializing inventory...")
        # 1 item left to demonstrate concurrency on water
        inv_burger = Inventory(product_id=p_burger.id, quantity=100, low_stock_threshold=30)
        inv_salad = Inventory(product_id=p_salad.id, quantity=50, low_stock_threshold=15)
        inv_water = Inventory(product_id=p_water.id, quantity=1, low_stock_threshold=10) # Concurrency target
        db.session.add_all([inv_burger, inv_salad, inv_water])
        db.session.commit()

        print("Creating suppliers...")
        sup1 = Supplier(name="Fresh Foods Co", email="orders@freshfoods.com", phone="123456789", status="ACTIVE", lead_time=1)
        db.session.add(sup1)
        db.session.commit()
        
        sp1 = SupplierProduct(supplier_id=sup1.id, product_id=p_burger.id, purchase_price=2.00, lead_time=1, is_preferred=True)
        db.session.add(sp1)
        db.session.commit()

        print("Seed data completed successfully. Use admin@canteen.com / demo123 to login.")

if __name__ == "__main__":
    seed()
