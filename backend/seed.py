import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import db
from app.models import User, Stall, Category, Product, Inventory, Organization, Institution, Campus, Canteen, Subscription

def seed_database():
    app = create_app('development')
    with app.app_context():
        # WARNING: This drops all tables and recreates them! 
        # For a hackathon MVP this is okay, but NEVER do this in real production!
        db.drop_all()
        db.create_all()

        from werkzeug.security import generate_password_hash
        hashed_pass = generate_password_hash('password123')
        
        print("Seeding Organization and Hierarchy...")
        org = Organization(name='Tech Corp Global', status='ACTIVE', plan='ENTERPRISE')
        db.session.add(org)
        db.session.commit()

        sub = Subscription(organization_id=org.id, plan_id='ENTERPRISE', status='ACTIVE')
        db.session.add(sub)
        
        inst = Institution(organization_id=org.id, name='Tech Corp HQ', status='ACTIVE')
        db.session.add(inst)
        db.session.commit()
        
        camp = Campus(organization_id=org.id, institution_id=inst.id, name='North Campus', status='ACTIVE')
        db.session.add(camp)
        db.session.commit()
        
        canteen = Canteen(organization_id=org.id, campus_id=camp.id, name='Main Cafeteria', status='ACTIVE')
        db.session.add(canteen)
        db.session.commit()

        print("Seeding Users...")
        admin = User(email='admin@example.com', password_hash=hashed_pass, name='Admin', role='ORG_ADMIN', organization_id=org.id)
        manager = User(email='manager@example.com', password_hash=hashed_pass, name='Manager', role='CANTEEN_MANAGER', organization_id=org.id)
        cashier = User(email='cashier@example.com', password_hash=hashed_pass, name='Cashier', role='CASHIER', organization_id=org.id)
        kitchen = User(email='kitchen@example.com', password_hash=hashed_pass, name='Kitchen', role='KITCHEN_STAFF', organization_id=org.id)
        db.session.add_all([admin, manager, cashier, kitchen])
        db.session.commit()

        print("Seeding Stalls...")
        burger_stall = Stall(organization_id=org.id, canteen_id=canteen.id, name='Burger Stall', description='Delicious Burgers')
        pizza_stall = Stall(organization_id=org.id, canteen_id=canteen.id, name='Pizza Stall', description='Fresh Pizza')
        db.session.add_all([burger_stall, pizza_stall])
        db.session.commit()

        # Assign kitchen staff to a stall
        kitchen.stall_id = burger_stall.id
        db.session.commit()

        print("Seeding Categories...")
        burgers = Category(name='Burgers', description='All kinds of burgers')
        pizzas = Category(name='Pizza', description='All kinds of pizzas')
        beverages = Category(name='Beverages', description='Cold drinks')
        db.session.add_all([burgers, pizzas, beverages])
        db.session.commit()

        print("Seeding Products...")
        chicken_burger = Product(organization_id=org.id, name='Chicken Burger', category_id=burgers.id, stall_id=burger_stall.id, price=100.0, preparation_time=5)
        veg_burger = Product(organization_id=org.id, name='Veg Burger', category_id=burgers.id, stall_id=burger_stall.id, price=80.0, preparation_time=4)
        margherita = Product(organization_id=org.id, name='Margherita Pizza', category_id=pizzas.id, stall_id=pizza_stall.id, price=200.0, preparation_time=10)
        coke = Product(organization_id=org.id, name='Coke', category_id=beverages.id, stall_id=burger_stall.id, price=40.0, preparation_time=1)
        db.session.add_all([chicken_burger, veg_burger, margherita, coke])
        db.session.commit()

        print("Seeding Inventory...")
        db.session.add(Inventory(product_id=chicken_burger.id, quantity=10, low_stock_threshold=2))
        db.session.add(Inventory(product_id=veg_burger.id, quantity=20, low_stock_threshold=5))
        db.session.add(Inventory(product_id=margherita.id, quantity=15, low_stock_threshold=3))
        db.session.add(Inventory(product_id=coke.id, quantity=50, low_stock_threshold=10))
        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
