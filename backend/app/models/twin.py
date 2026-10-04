from ..extensions import db
from datetime import datetime, timezone
import json

class OperationalSnapshot(db.Model):
    """
    Milestone 4: Operational Snapshots
    Represents an immutable, point-in-time snapshot of the operational state (Digital Twin).
    """
    __tablename__ = 'operational_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Snapshot metadata
    name = db.Column(db.String(255), nullable=True) # E.g., "Campus lunch operation — 12:15 PM"
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    source_event_id = db.Column(db.String(50), nullable=True) # If triggered by a specific event
    version = db.Column(db.String(50), default='v1.0')
    
    # State data (JSON) - ensuring it does not override live operational state
    # Conceptual structure: { canteens: [...], inventory: [...], queues: [...], ... }
    state_data = db.Column(db.JSON, nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<OperationalSnapshot {self.id} at {self.timestamp}>"

class SimulationScenario(db.Model):
    """
    Milestone 5: Scenario Engine
    Defines the parameters and constraints applied to a snapshot for a What-If simulation.
    """
    __tablename__ = 'simulation_scenarios'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scenario_type = db.Column(db.String(50), nullable=False) # e.g. 'DEMAND_SURGE', 'KITCHEN_FAILURE'
    
    base_snapshot_id = db.Column(db.Integer, db.ForeignKey('operational_snapshots.id', ondelete='CASCADE'), nullable=False)
    
    # Parameters for the scenario (e.g., {"demand_multiplier": 1.3, "unavailable_stations": [2]})
    parameters = db.Column(db.JSON, nullable=False)
    
    # Milestone 35: Optimization objective (e.g., 'MINIMIZE_WAIT_TIME')
    optimization_objective = db.Column(db.String(100), nullable=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    snapshot = db.relationship('OperationalSnapshot')

class SimulationResult(db.Model):
    """
    Milestone 6: Basic what-if simulation output
    """
    __tablename__ = 'simulation_results'

    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('simulation_scenarios.id', ondelete='CASCADE'), nullable=False)
    
    # Expected outcomes
    result_data = db.Column(db.JSON, nullable=False)
    
    # Milestone 20: Confidence and uncertainty representation
    confidence_score = db.Column(db.Float, nullable=True)
    uncertainty_range = db.Column(db.JSON, nullable=True)
    
    # Milestone 19: Constraint violations detected during simulation
    constraint_violations = db.Column(db.JSON, nullable=True)
    
    # Execution metadata
    model_version = db.Column(db.String(50), nullable=False, default='v1.0')
    status = db.Column(db.String(50), nullable=False, default='COMPLETED') # QUEUED, RUNNING, COMPLETED, FAILED
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    scenario = db.relationship('SimulationScenario', backref=db.backref('results', lazy=True))

class OperationalRisk(db.Model):
    """
    Milestone 72: Risk Engine
    Tracks active and simulated risks.
    """
    __tablename__ = 'operational_risks'
    
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    risk_type = db.Column(db.String(50), nullable=False) # e.g. 'INVENTORY_STOCKOUT', 'SUPPLIER_DELAY'
    title = db.Column(db.String(255), nullable=False)
    
    # Risk scoring (Milestone 73)
    probability = db.Column(db.Float, nullable=False) # 0.0 to 1.0
    impact_score = db.Column(db.Float, nullable=False) # e.g. 1 to 10
    urgency = db.Column(db.String(50), nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    
    context_data = db.Column(db.JSON, nullable=True)
    
    # If derived from a simulation
    simulation_result_id = db.Column(db.Integer, db.ForeignKey('simulation_results.id', ondelete='CASCADE'), nullable=True)
    
    status = db.Column(db.String(50), nullable=False, default='ACTIVE') # ACTIVE, MITIGATED, MATERIALIZED
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class OperationalPlaybook(db.Model):
    """
    Milestone 81: Operational Playbooks
    Pre-defined contingency plans.
    """
    __tablename__ = 'operational_playbooks'
    
    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    name = db.Column(db.String(255), nullable=False)
    trigger_condition = db.Column(db.String(255), nullable=False)
    
    # JSON schema defining immediate action, escalation, fallback, recovery
    playbook_steps = db.Column(db.JSON, nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class DecisionOutcome(db.Model):
    """
    Milestone 51: Decision Effectiveness
    Tracks the expected vs actual outcome of an executed recommendation.
    """
    __tablename__ = 'decision_outcomes'
    
    id = db.Column(db.Integer, primary_key=True)
    recommendation_id = db.Column(db.Integer, db.ForeignKey('recommendations.id', ondelete='CASCADE'), nullable=False)
    
    expected_outcome = db.Column(db.JSON, nullable=False)
    actual_outcome = db.Column(db.JSON, nullable=True) # Filled post-action validation
    
    difference_score = db.Column(db.Float, nullable=True) # How far off was the prediction?
    
    evaluated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
