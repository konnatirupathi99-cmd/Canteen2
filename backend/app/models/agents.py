from ..extensions import db
from datetime import datetime, timezone

class AgentRegistry(db.Model):
    """
    Milestone 2 & 3: Agent Registry & Identity
    Tracks the version, capabilities, and health of specialized agents.
    """
    __tablename__ = 'agent_registry'

    id = db.Column(db.String(50), primary_key=True) # e.g., 'INVENTORY_AGENT'
    name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20), nullable=False, default='v1.0')
    
    purpose = db.Column(db.String(255), nullable=False)
    
    # JSON list of allowed tools (e.g. ['get_inventory', 'request_transfer'])
    allowed_tools = db.Column(db.JSON, nullable=False, default=list)
    
    status = db.Column(db.String(20), nullable=False, default='ACTIVE') # ACTIVE, PAUSED, DISABLED, DEGRADED, ERROR
    scope = db.Column(db.String(20), nullable=False, default='LOCAL') # LOCAL, CAMPUS, INSTITUTION, ENTERPRISE
    
    failure_count = db.Column(db.Integer, default=0)
    last_execution_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Agent {self.id} ({self.status})>"

class AgentTask(db.Model):
    """
    Milestone 4: Agent Task System
    Tracks discrete tasks dispatched to agents.
    """
    __tablename__ = 'agent_tasks'
    
    id = db.Column(db.String(50), primary_key=True) # UUID
    agent_id = db.Column(db.String(50), db.ForeignKey('agent_registry.id'), nullable=False, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('canteens.id', ondelete='CASCADE'), nullable=True, index=True) # canteens act as campuses in MVP
    scope = db.Column(db.String(20), nullable=False, default='LOCAL')
    
    trigger_event = db.Column(db.String(100), nullable=True) # e.g. 'INVENTORY_LOW'
    correlation_id = db.Column(db.String(100), nullable=False, index=True)
    priority = db.Column(db.String(20), default='MEDIUM') # CRITICAL, HIGH, MEDIUM, LOW
    
    input_payload = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='PENDING') # PENDING, RUNNING, WAITING, COMPLETED, FAILED, ESCALATED
    
    result_payload = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

class AgentToolExecution(db.Model):
    """
    Milestone 5: Tool Framework & Audit
    Records every tool executed by an agent.
    """
    __tablename__ = 'agent_tool_executions'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(50), db.ForeignKey('agent_tasks.id', ondelete='CASCADE'), nullable=False)
    agent_id = db.Column(db.String(50), db.ForeignKey('agent_registry.id'), nullable=False)
    
    tool_name = db.Column(db.String(100), nullable=False)
    input_args = db.Column(db.JSON, nullable=False)
    output_result = db.Column(db.JSON, nullable=True)
    
    is_high_risk = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    executed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
