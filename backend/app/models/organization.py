from ..extensions import db
from datetime import datetime

class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='TRIAL') # TRIAL, ACTIVE, SUSPENDED, GRACE_PERIOD, CANCELLED, ARCHIVED
    plan = db.Column(db.String(50), nullable=False, default='STARTER') # STARTER, PROFESSIONAL, ENTERPRISE
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Organization {self.name}>"

class Institution(db.Model):
    __tablename__ = 'institutions'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='ACTIVE') # ACTIVE, SUSPENDED
    
    default_currency = db.Column(db.String(10), nullable=False, default='INR')
    timezone = db.Column(db.String(50), nullable=False, default='UTC')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    campuses = db.relationship('Campus', backref='institution', lazy='dynamic')

    def __repr__(self):
        return f"<Institution {self.name}>"

class Campus(db.Model):
    __tablename__ = 'campuses'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='ACTIVE')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    canteens = db.relationship('Canteen', backref='campus', lazy='dynamic')

    def __repr__(self):
        return f"<Campus {self.name}>"

class Canteen(db.Model):
    __tablename__ = 'canteens'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='ACTIVE') # ACTIVE, PLANNED, SUSPENDED, CLOSED
    
    opening_time = db.Column(db.Time, nullable=True)
    closing_time = db.Column(db.Time, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stalls = db.relationship('Stall', backref='canteen', lazy='dynamic')

    def __repr__(self):
        return f"<Canteen {self.name}>"

class OrganizationMembership(db.Model):
    """
    Links a user to a specific scope (Institution, Campus, Canteen, or Stall)
    along with their role in that scope.
    """
    __tablename__ = 'organization_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Scope resolution
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('campuses.id', ondelete='CASCADE'), nullable=True, index=True)
    canteen_id = db.Column(db.Integer, db.ForeignKey('canteens.id', ondelete='CASCADE'), nullable=True, index=True)
    stall_id = db.Column(db.Integer, db.ForeignKey('stalls.id', ondelete='CASCADE'), nullable=True, index=True)
    
    role = db.Column(db.String(50), nullable=False) # SYSTEM_ADMIN, INSTITUTION_ADMIN, CAMPUS_ADMIN, CANTEEN_MANAGER, STALL_MANAGER, KITCHEN_STAFF, CASHIER
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='memberships')

    def __repr__(self):
        return f"<OrganizationMembership User:{self.user_id} Role:{self.role}>"
