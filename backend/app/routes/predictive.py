from flask import Blueprint, jsonify, request
from app.models.predictive import Forecast, ForecastOverride, PreparationPlan, WasteRecord, DemandEvent
from app.models.product import Product
from app.models.inventory import Inventory
from app.extensions import db
from app.auth.middleware import require_auth, require_role
from app.services.forecasting_service import ForecastingService
from app.services.inventory_service import InventoryService
from datetime import datetime, timedelta

predictive_bp = Blueprint('predictive', __name__, url_prefix='/api/v1/predictive')

@predictive_bp.route('/forecasts/generate', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def generate_forecasts(current_user):
    data = request.get_json() or {}
    product_id = data.get('product_id')
    
    target_date = datetime.utcnow().date() + timedelta(days=1)
    if 'target_date' in data:
        target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()
        
    products = [Product.query.get(product_id)] if product_id else Product.query.filter_by(status='ACTIVE').all()
    
    generated = []
    for p in products:
        if not p: continue
        f = ForecastingService.generate_and_save_forecast(p.id, target_date)
        generated.append({
            "product_id": p.id,
            "predicted_quantity": f.predicted_quantity,
            "confidence": f.confidence
        })
        
    return jsonify(success=True, data=generated)

@predictive_bp.route('/forecasts/<int:forecast_id>/override', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def override_forecast(current_user, forecast_id):
    data = request.get_json()
    new_quantity = data.get('new_quantity')
    reason = data.get('reason')
    
    if new_quantity is None or not reason:
        return jsonify(success=False, error={"code": "VALIDATION_ERROR", "message": "new_quantity and reason required"}), 400
        
    forecast = Forecast.query.get(forecast_id)
    if not forecast:
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "Forecast not found"}), 404
        
    override = ForecastOverride(
        forecast_id=forecast.id,
        overridden_by=current_user.id,
        new_quantity=new_quantity,
        reason=reason
    )
    db.session.add(override)
    db.session.commit()
    
    return jsonify(success=True, data={"id": override.id, "new_quantity": new_quantity})

@predictive_bp.route('/preparation-plans', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER', 'KITCHEN_STAFF'])
def get_preparation_plans(current_user):
    plans = PreparationPlan.query.filter_by(plan_date=datetime.utcnow().date()).all()
    return jsonify(success=True, data=[{
        "id": p.id,
        "product_name": p.product.name,
        "recommended_quantity": p.recommended_quantity,
        "final_quantity": p.final_quantity,
        "status": p.status
    } for p in plans])

@predictive_bp.route('/preparation-plans', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def create_preparation_plan(current_user):
    data = request.get_json()
    product_id = data.get('product_id')
    recommended = data.get('recommended_quantity')
    final = data.get('final_quantity', recommended)
    
    plan = PreparationPlan(
        product_id=product_id,
        plan_date=datetime.utcnow().date(),
        recommended_quantity=recommended,
        final_quantity=final,
        created_by=current_user.id
    )
    db.session.add(plan)
    db.session.commit()
    return jsonify(success=True, data={"id": plan.id})

@predictive_bp.route('/waste', methods=['POST'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER', 'STALL_MANAGER', 'KITCHEN_STAFF'])
def record_waste(current_user):
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    reason = data.get('reason')
    category = data.get('category', 'OTHER')
    
    if not product_id or not quantity or quantity <= 0 or not reason:
        return jsonify(success=False, error={"code": "VALIDATION_ERROR"}), 400
        
    # Check idempotency: simple check if same user reported same amount for same product in last 5 mins
    five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
    existing = WasteRecord.query.filter_by(
        product_id=product_id,
        quantity=quantity,
        recorded_by=current_user.id
    ).filter(WasteRecord.recorded_at >= five_mins_ago).first()
    
    if existing:
        return jsonify(success=True, data={"id": existing.id, "message": "Duplicate ignored"}), 200
        
    waste = WasteRecord(
        product_id=product_id,
        stall_id=data.get('stall_id'),
        quantity=quantity,
        reason=reason,
        category=category,
        recorded_by=current_user.id
    )
    db.session.add(waste)
    
    # Deduct from inventory safely via Phase 7 mechanism
    # (If the waste implies we lost standard inventory, else if preparation waste it might be different, but for MVP deduct standard inventory)
    InventoryService.validate_and_decrement(
        product_id=product_id,
        quantity=quantity,
        user_id=current_user.id,
        reference_id=f"WASTE"
    )
    
    # Alert if high waste
    # E.g., if > 10% of total stock
    inv = Inventory.query.filter_by(product_id=product_id).first()
    if inv and quantity > (inv.quantity * 0.1):
        from app.services.alert_service import AlertService
        AlertService.trigger_alert(
            alert_type='HIGH_WASTE',
            severity='HIGH',
            message=f"High waste recorded for Product {product_id} ({quantity} portions)",
            product_id=product_id,
            deduplication_key=f"waste_{product_id}"
        )

    db.session.commit()
    
    return jsonify(success=True, data={"id": waste.id}), 201

@predictive_bp.route('/dashboard', methods=['GET'])
@require_auth
@require_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_predictive_dashboard(current_user):
    products = Product.query.filter_by(status='ACTIVE').all()
    dashboard = []
    
    today = datetime.utcnow().date()
    
    for p in products:
        f_today = Forecast.query.filter_by(product_id=p.id, forecast_date=today, status='ACTIVE').first()
        risk, proj, eta = ForecastingService.predict_stockout(p.id)
        
        item = {
            "product_id": p.id,
            "name": p.name,
            "forecast_today": f_today.predicted_quantity if f_today else 0,
            "confidence": f_today.confidence if f_today else 'UNKNOWN',
            "stockout_risk": risk,
            "projected_inventory": proj,
            "stockout_eta": eta.isoformat() if eta else None
        }
        dashboard.append(item)
        
    return jsonify(success=True, data={"products": dashboard})
