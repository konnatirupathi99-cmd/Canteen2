from app.extensions import db
from datetime import datetime, timezone
import uuid

class DeveloperApp(db.Model):
    """
    Milestone 10: Developer Application Registry
    Represents an external integration/application registered on the platform.
    """
    __tablename__ = 'developer_apps'

    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False, index=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    status = db.Column(db.String(20), nullable=False, default='ACTIVE') # ACTIVE, SUSPENDED, REVOKED
    environment = db.Column(db.String(20), nullable=False, default='PRODUCTION') # SANDBOX, PRODUCTION
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    api_keys = db.relationship('ApiKey', backref='app', lazy=True, cascade='all, delete-orphan')
    webhooks = db.relationship('WebhookSubscription', backref='app', lazy=True, cascade='all, delete-orphan')

class ApiKey(db.Model):
    """
    Milestone 11: API Key Management
    Securely tracks hashed API keys assigned to Developer Apps.
    """
    __tablename__ = 'api_keys'

    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = db.Column(db.String(50), db.ForeignKey('developer_apps.id', ondelete='CASCADE'), nullable=False)
    
    key_hash = db.Column(db.String(255), nullable=False) # Store only the hash, never the raw key
    prefix = db.Column(db.String(10), nullable=False) # e.g. 'ctn_prod_XXXX' for identification
    
    scopes = db.Column(db.JSON, nullable=False, default=list) # e.g. ['orders:read', 'inventory:write']
    
    expires_at = db.Column(db.DateTime, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class WebhookSubscription(db.Model):
    """
    Milestone 13: Webhook Infrastructure
    Registers an external URL to receive specific event payloads.
    """
    __tablename__ = 'webhook_subscriptions'

    id = db.Column(db.String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    app_id = db.Column(db.String(50), db.ForeignKey('developer_apps.id', ondelete='CASCADE'), nullable=False)
    
    endpoint_url = db.Column(db.String(500), nullable=False)
    secret = db.Column(db.String(255), nullable=False) # Used for HMAC payload signing
    
    event_types = db.Column(db.JSON, nullable=False) # e.g. ['order.created', 'inventory.low']
    
    is_active = db.Column(db.Boolean, default=True)
    failure_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
