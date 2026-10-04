from app.extensions import db
from datetime import datetime
import uuid
import json

class AutomationPolicy(db.Model):
    """
    Milestone 4: Automation Policy Data Model
    Determines what autonomous actions are allowed, under what conditions, and with what limits.
    """
    __tablename__ = 'automation_policies'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.Integer, nullable=True, index=True) # Scope: Institution/Tenant
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Execution Rules
    trigger_event = db.Column(db.String(100), nullable=False) # e.g. STOCKOUT_RISK_HIGH
    conditions = db.Column(db.Text, nullable=False) # JSON: {"stockout_probability": {">": 80}, "item_active": True}
    action_type = db.Column(db.String(100), nullable=False) # e.g. GENERATE_REPLENISHMENT
    
    # Autonomy Level (Milestone 2, 3)
    # LEVEL_1: Analyze, LEVEL_2: Recommend, LEVEL_3: Approval Required, LEVEL_4: Autonomous
    autonomy_level = db.Column(db.String(20), nullable=False, default='LEVEL_3') 
    
    # Safety Limits (Milestone 25)
    limits = db.Column(db.Text, nullable=True) # JSON: {"max_quantity": 50, "max_financial_impact": 500}
    cooldown_minutes = db.Column(db.Integer, default=60) # Milestone 26
    
    status = db.Column(db.String(20), nullable=False, default='DRAFT') # DRAFT, TESTING, ACTIVE, PAUSED, DEPRECATED
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def get_conditions(self):
        return json.loads(self.conditions) if self.conditions else {}
        
    def get_limits(self):
        return json.loads(self.limits) if self.limits else {}


class AutomationExecution(db.Model):
    """
    Milestone 29: Automation Audit
    Records every autonomous or policy-driven action taken by the system.
    """
    __tablename__ = 'automation_executions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_id = db.Column(db.String(36), db.ForeignKey('automation_policies.id'), nullable=True)
    tenant_id = db.Column(db.Integer, nullable=True, index=True)
    
    trigger_event = db.Column(db.String(100), nullable=False)
    action_type = db.Column(db.String(100), nullable=False)
    
    # Correlation and Idempotency (Milestone 27, 29)
    correlation_id = db.Column(db.String(100), nullable=True, index=True)
    idempotency_key = db.Column(db.String(100), nullable=True, unique=True)
    
    status = db.Column(db.String(20), nullable=False) # SUCCESS, FAILED, BLOCKED, DRY_RUN
    reason = db.Column(db.Text, nullable=True) # Why it succeeded/failed/blocked
    
    system_state_before = db.Column(db.Text, nullable=True) # JSON
    action_payload = db.Column(db.Text, nullable=True) # JSON
    result = db.Column(db.Text, nullable=True) # JSON
    
    executed_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
