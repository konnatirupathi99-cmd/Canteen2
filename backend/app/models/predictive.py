from ..extensions import db
from datetime import datetime

class Forecast(db.Model):
    __tablename__ = 'forecasts'

    id = db.Column(db.Integer, primary_key=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    
    forecast_date = db.Column(db.Date, nullable=False, index=True)
    forecast_period = db.Column(db.String(50), nullable=False, default='DAY') # e.g., 'DAY', 'LUNCH', 'DINNER'
    
    predicted_quantity = db.Column(db.Integer, nullable=False)
    confidence = db.Column(db.String(50), nullable=False, default='MEDIUM') # LOW, MEDIUM, HIGH
    model_type = db.Column(db.String(50), nullable=False) # e.g., 'MOVING_AVERAGE', 'WEIGHTED_AVERAGE'
    model_version = db.Column(db.String(50), nullable=False, default='v1.0')
    
    # Model Monitoring (Milestone 10)
    actual_quantity = db.Column(db.Integer, nullable=True) # Updated post-factum
    mean_absolute_error = db.Column(db.Float, nullable=True)
    model_drift_detected = db.Column(db.Boolean, default=False)
    
    status = db.Column(db.String(50), nullable=False, default='ACTIVE', index=True) # ACTIVE, SUPERSEDED
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    product = db.relationship('Product')
    overrides = db.relationship('ForecastOverride', backref='forecast', lazy='dynamic')

# Alias for backwards compatibility
PredictiveForecast = Forecast


class ForecastOverride(db.Model):
    __tablename__ = 'forecast_overrides'
    
    id = db.Column(db.Integer, primary_key=True)
    forecast_id = db.Column(db.Integer, db.ForeignKey('forecasts.id', ondelete='CASCADE'), nullable=False, index=True)
    overridden_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    new_quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')


class PreparationPlan(db.Model):
    __tablename__ = 'preparation_plans'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    
    plan_date = db.Column(db.Date, nullable=False, index=True)
    meal_period = db.Column(db.String(50), nullable=False, default='DAY')
    
    recommended_quantity = db.Column(db.Integer, nullable=False)
    final_quantity = db.Column(db.Integer, nullable=False)
    
    status = db.Column(db.String(50), nullable=False, default='RECOMMENDED', index=True) # RECOMMENDED, ACCEPTED, MODIFIED, IN_PROGRESS, COMPLETED
    override_reason = db.Column(db.String(255), nullable=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship('Product')


class WasteRecord(db.Model):
    __tablename__ = 'waste_records'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    stall_id = db.Column(db.Integer, db.ForeignKey('stalls.id', ondelete='SET NULL'), nullable=True, index=True)
    
    quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(50), nullable=False, default='Portion')
    
    reason = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False) # PREPARATION_WASTE, UNSOLD_WASTE, DAMAGE, EXPIRY, OTHER
    
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    product = db.relationship('Product')
    stall = db.relationship('Stall')
    user = db.relationship('User')


class DemandEvent(db.Model):
    __tablename__ = 'demand_events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    event_date = db.Column(db.Date, nullable=False, index=True)
    
    expected_attendance = db.Column(db.Integer, nullable=True)
    demand_multiplier = db.Column(db.Numeric(4, 2), nullable=False, default=1.0) # e.g. 1.25 for +25%
    
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class DemandAnomaly(db.Model):
    __tablename__ = 'demand_anomalies'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False, index=True)
    
    baseline = db.Column(db.Numeric(10, 2), nullable=False)
    observed = db.Column(db.Numeric(10, 2), nullable=False)
    deviation_percentage = db.Column(db.Numeric(10, 2), nullable=False)
    
    anomaly_type = db.Column(db.String(50), nullable=False) # DEMAND_SPIKE, DEMAND_DROP
    detected_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    product = db.relationship('Product')
