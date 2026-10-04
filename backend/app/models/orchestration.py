from datetime import datetime, timezone
import uuid
import json
from app.extensions import db

class Workflow(db.Model):
    """
    Phase 25: Operational Orchestrator Workflow Model
    Tracks long-running, multi-step processes securely and idempotently.
    """
    __tablename__ = 'workflows'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False) # e.g. 'DemandSpikeMitigation'
    version = db.Column(db.String(20), nullable=False, default='v1.0')
    
    correlation_id = db.Column(db.String(100), nullable=False, index=True) # E.g., event ID
    idempotency_key = db.Column(db.String(100), nullable=False, unique=True)
    
    status = db.Column(db.String(20), nullable=False, default='CREATED') 
    # CREATED, VALIDATING, RUNNING, WAITING, PAUSED, COMPLETED, FAILED, CANCELLED, COMPENSATING, RECOVERED
    
    context_data = db.Column(db.Text, nullable=True) # JSON
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    steps = db.relationship('WorkflowStep', backref='workflow', lazy=True, cascade='all, delete-orphan')

class WorkflowStep(db.Model):
    """
    Phase 25: Operational Orchestrator Workflow Step
    Tracks the execution state of individual actions within a workflow.
    """
    __tablename__ = 'workflow_steps'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = db.Column(db.String(36), db.ForeignKey('workflows.id', ondelete='CASCADE'), nullable=False)
    
    step_name = db.Column(db.String(100), nullable=False)
    action_type = db.Column(db.String(100), nullable=False) # e.g. 'EvaluateInventory'
    
    status = db.Column(db.String(20), nullable=False, default='PENDING') # PENDING, RUNNING, COMPLETED, FAILED
    
    input_data = db.Column(db.Text, nullable=True) # JSON
    output_data = db.Column(db.Text, nullable=True) # JSON
    error_message = db.Column(db.Text, nullable=True)
    
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

class OperationalIncident(db.Model):
    """
    Phase 25: Anomaly Engine & Incident Management
    Tracks anomalies and coordinates resolution across operators and automation.
    """
    __tablename__ = 'operational_incidents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False, index=True)
    
    title = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(20), nullable=False) # INFO, LOW, MEDIUM, HIGH, CRITICAL
    status = db.Column(db.String(20), nullable=False, default='OPEN') 
    # OPEN, INVESTIGATING, MITIGATING, MONITORING, RESOLVED, CLOSED
    
    anomaly_type = db.Column(db.String(50), nullable=False) # e.g. 'VolumeAnomaly', 'InventoryAnomaly'
    affected_service = db.Column(db.String(50), nullable=True)
    root_cause = db.Column(db.Text, nullable=True)
    
    context_data = db.Column(db.Text, nullable=True) # JSON describing the anomaly evidence
    
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    workflow_id = db.Column(db.String(36), db.ForeignKey('workflows.id', ondelete='SET NULL'), nullable=True)
    
    detected_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)
    
class DigitalTwinHealth(db.Model):
    """
    Phase 25: Digital Twin Continuous Synchronization
    Monitors the health and divergence of the Digital Twin state.
    """
    __tablename__ = 'digital_twin_health'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    last_synced_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    event_lag_ms = db.Column(db.Integer, default=0)
    
    state_divergence_score = db.Column(db.Float, default=0.0) # 0.0 (perfect) to 1.0 (completely divergent)
    status = db.Column(db.String(20), nullable=False, default='HEALTHY') # HEALTHY, DEGRADED, STALE, UNAVAILABLE
    
    last_reconciliation_at = db.Column(db.DateTime, nullable=True)
