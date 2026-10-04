import pytest
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models import User, Stall, Category, Product, Inventory, InventoryTransaction, Order, OrderItem, OrderStatusHistory, AuditLog

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_database_tables_exist(app):
    """Test that all required models can be created successfully in the test DB."""
    # If the app context initializes without errors and db.create_all() passes, 
    # the models are syntactically and structurally correct for SQLAlchemy.
    with app.app_context():
        # Querying the tables to ensure they exist
        assert db.session.query(User).count() == 0
        assert db.session.query(Stall).count() == 0
        assert db.session.query(Category).count() == 0
        assert db.session.query(Product).count() == 0
        assert db.session.query(Inventory).count() == 0
        assert db.session.query(InventoryTransaction).count() == 0
        assert db.session.query(Order).count() == 0
        assert db.session.query(OrderItem).count() == 0
        assert db.session.query(OrderStatusHistory).count() == 0
        assert db.session.query(AuditLog).count() == 0
