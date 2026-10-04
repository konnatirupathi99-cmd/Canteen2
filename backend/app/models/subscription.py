from ..extensions import db
from datetime import datetime

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    
    plan_id = db.Column(db.String(50), nullable=False) # e.g. 'STARTER', 'PROFESSIONAL', 'ENTERPRISE'
    status = db.Column(db.String(50), nullable=False, default='TRIAL') # TRIAL, ACTIVE, PAST_DUE, PAUSED, CANCELLED, EXPIRED
    
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    renewal_date = db.Column(db.DateTime, nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    billing_provider = db.Column(db.String(50), nullable=True) # e.g. 'stripe', 'internal'
    billing_reference_id = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship('Organization', backref=db.backref('subscription', uselist=False))

class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True, index=True)
    
    invoice_number = db.Column(db.String(100), nullable=False, unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='USD')
    status = db.Column(db.String(50), nullable=False, default='DRAFT') # DRAFT, OPEN, PAID, UNCOLLECTIBLE, VOID
    
    billing_period_start = db.Column(db.DateTime, nullable=True)
    billing_period_end = db.Column(db.DateTime, nullable=True)
    
    provider_reference = db.Column(db.String(100), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship('Organization')
    subscription = db.relationship('Subscription')

class Entitlement(db.Model):
    """Specific commercial features/limits granted to an organization."""
    __tablename__ = 'entitlements'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    
    feature_key = db.Column(db.String(100), nullable=False, index=True) # e.g. 'advanced_analytics', 'max_users'
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    limit_value = db.Column(db.Integer, nullable=True) # Used if the entitlement is a numerical limit
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = db.relationship('Organization', backref='entitlements')

class UsageRecord(db.Model):
    """Near real-time usage tracking for metered limits."""
    __tablename__ = 'usage_records'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    
    metric_key = db.Column(db.String(100), nullable=False, index=True) # e.g. 'api_calls', 'active_users'
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    
    current_value = db.Column(db.Integer, nullable=False, default=0)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship('Organization')
