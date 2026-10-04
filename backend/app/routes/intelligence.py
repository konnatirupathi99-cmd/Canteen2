from flask import Blueprint, jsonify, request
from app.auth.middleware import require_auth, require_tenant_role
from app.services.intelligence_service import IntelligenceService
from app.models import IntelligenceSignal, Recommendation, RecommendationAudit, BusinessIncident
from app.extensions import db

intelligence_bp = Blueprint('intelligence', __name__, url_prefix='/api/v1/intelligence')

@intelligence_bp.route('/incidents', methods=['GET'])
@require_auth
@require_tenant_role(['CANTEEN_MANAGER', 'ORG_ADMIN'])
def get_incidents(current_user):
    institution_id = request.args.get('institution_id')
    incidents = BusinessIncident.query.filter_by(
        institution_id=institution_id,
        status='OPEN'
    ).order_by(BusinessIncident.created_at.desc()).all()
    
    return jsonify(success=True, incidents=[{
        "id": i.id,
        "title": i.title,
        "type": i.incident_type,
        "severity": i.severity,
        "status": i.status,
        "created_at": i.created_at.isoformat()
    } for i in incidents])

@intelligence_bp.route('/snapshot', methods=['GET'])
@require_auth
@require_tenant_role(['CANTEEN_MANAGER', 'ORG_ADMIN'])
def get_snapshot(current_user):
    """
    Returns the real-time operational snapshot.
    """
    snapshot = IntelligenceService.get_real_time_snapshot()
    return jsonify(success=True, snapshot=snapshot)


@intelligence_bp.route('/signals', methods=['GET'])
@require_auth
@require_tenant_role(['CANTEEN_MANAGER', 'ORG_ADMIN'])
def get_signals(current_user):
    """
    Returns active intelligence signals (anomalies).
    """
    signals = IntelligenceSignal.query.filter_by(status='OPEN').order_by(IntelligenceSignal.created_at.desc()).limit(50).all()
    return jsonify(success=True, signals=[{
        "id": s.id,
        "type": s.type,
        "severity": s.severity,
        "message": s.message,
        "context": s.get_context(),
        "created_at": s.created_at.isoformat()
    } for s in signals])


@intelligence_bp.route('/recommendations', methods=['GET'])
@require_auth
@require_tenant_role(['CANTEEN_MANAGER', 'ORG_ADMIN'])
def get_recommendations(current_user):
    """
    Returns active recommendations, ranked by Priority and Confidence.
    """
    recs = Recommendation.query.filter_by(status='GENERATED').all()
    
    # Priority mapping for sorting
    priority_weights = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    
    # Sort in-memory to handle the calculated ranking
    recs.sort(key=lambda r: (priority_weights.get(r.priority, 0), r.confidence, r.created_at), reverse=True)
    
    return jsonify(success=True, recommendations=[{
        "id": r.id,
        "type": r.type,
        "priority": r.priority,
        "reason": r.reason,
        "confidence": r.confidence,
        "suggested_action": r.get_action(),
        "created_at": r.created_at.isoformat()
    } for r in recs])


@intelligence_bp.route('/recommendations/<rec_id>/decide', methods=['POST'])
@require_auth
@require_tenant_role(['CANTEEN_MANAGER', 'ORG_ADMIN'])
def decide_recommendation(current_user, rec_id):
    """
    Milestone 9: Human Approval Workflow
    Milestone 12: Policy & Approval Engine Validation
    """
    data = request.get_json()
    decision = data.get('decision') # APPROVED, REJECTED, MODIFIED
    notes = data.get('notes', '')
    institution_id = request.args.get('institution_id') or request.json.get('institution_id')
    
    if decision not in ['APPROVED', 'REJECTED', 'MODIFIED']:
        return jsonify(success=False, error={"code": "INVALID_DECISION", "message": "Decision must be APPROVED, REJECTED, or MODIFIED"}), 400
        
    rec = Recommendation.query.get(rec_id)
    if not rec:
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "Recommendation not found"}), 404
        
    if rec.status != 'GENERATED':
        return jsonify(success=False, error={"code": "ALREADY_PROCESSED", "message": "Recommendation already processed"}), 400
        
    if decision == 'APPROVED':
        # Policy Check!
        from app.services.policy_service import PolicyService
        action_data = rec.get_action()
        
        if action_data.get('action') == 'create_purchase_order':
            # Needs price to validate amount, for simplicity let's use a mock amount or fetch from DB
            # We'll assume amount is passed in action_data or we skip for now
            qty = action_data.get('quantity', 0)
            
            # Since this is an MVP policy evaluation, we will evaluate based on qty * 10 (mock price)
            mock_amount = qty * 10
            requires_approval, reason = PolicyService.requires_approval('PURCHASE', mock_amount, institution_id)
            
            if requires_approval and current_user.role not in ['ORG_ADMIN', 'SYSTEM_ADMIN']:
                return jsonify(success=False, error={"code": "POLICY_RESTRICTION", "message": reason}), 403
                
    # Update recommendation status
    rec.status = decision
    rec.reviewed_by = current_user.id
    rec.reviewed_at = db.func.current_timestamp()
    
    # Audit log
    audit = RecommendationAudit(
        recommendation_id=rec.id,
        decision=decision,
        user_id=current_user.id,
        notes=notes
    )
    db.session.add(audit)
    db.session.commit()
    
    return jsonify(success=True, message=f"Recommendation {decision.lower()} successfully")


@intelligence_bp.route('/evaluate', methods=['POST'])
@require_auth
@require_tenant_role(['CANTEEN_MANAGER', 'ORG_ADMIN'])
def evaluate_intelligence(current_user):
    """
    Manually triggers the intelligence engine to scan all products.
    In production, this would be an asynchronous CRON job.
    """
    from app.models import Product
    products = Product.query.filter_by(status='ACTIVE').all()
    
    signals_generated = 0
    recs_generated = 0
    
    for p in products:
        # Check stockout risk
        sig = IntelligenceService.generate_stockout_risk_signal(p.id, p.stall_id)
        if sig:
            signals_generated += 1
            # Recommend reorder if risk
            if sig.severity in ['HIGH', 'CRITICAL']:
                IntelligenceService.create_recommendation(
                    type='REORDER',
                    reason=sig.message,
                    suggested_action={"action": "create_purchase_request", "product_id": p.id},
                    priority=sig.severity,
                    confidence=0.92,
                    product_id=p.id,
                    stall_id=p.stall_id
                )
                recs_generated += 1
                
        # Check demand surge
        d_sig, d_rec = IntelligenceService.generate_demand_surge_signal(p.id, p.stall_id)
        if d_sig:
            signals_generated += 1
        if d_rec:
            recs_generated += 1
            
        # Check supplier risk
        s_sig, s_rec = IntelligenceService.generate_supplier_risk_signal(p.id)
        if s_sig:
            signals_generated += 1
        if s_rec:
            recs_generated += 1
            
    from app.models import Stall
    stalls = Stall.query.all()
    for s in stalls:
        k_sig, k_rec = IntelligenceService.generate_kitchen_bottleneck_signal(s.id)
        if k_sig:
            signals_generated += 1
        if k_rec:
            recs_generated += 1
            
    return jsonify({
        "success": True, 
        "message": "Intelligence evaluation complete.",
        "signals_generated": signals_generated,
        "recommendations_generated": recs_generated
    })


@intelligence_bp.route('/simulate', methods=['POST'])
@require_auth
@require_tenant_role(['CANTEEN_MANAGER', 'ORG_ADMIN'])
def simulate(current_user):
    """
    Milestone 10: What-If Simulation endpoint
    """
    data = request.get_json()
    scenario_type = data.get('scenario_type')
    params = data.get('params', {})
    
    if not scenario_type:
        return jsonify(success=False, error={"code": "MISSING_DATA", "message": "scenario_type is required"}), 400
        
    result = IntelligenceService.simulate_scenario(scenario_type, params)
    
    if "error" in result:
        return jsonify(success=False, error={"code": "INVALID_SCENARIO", "message": result["error"]}), 400
        
    return jsonify(success=True, result=result)


@intelligence_bp.route('/benchmark', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN'])
def get_benchmarks(current_user):
    """
    Milestone 12: Cross-Canteen Intelligence & Benchmarking
    Compares performance across stalls.
    """
    from app.models import Stall, Fulfillment
    
    stalls = Stall.query.all()
    benchmarks = []
    
    for s in stalls:
        total_orders = Fulfillment.query.filter_by(stall_id=s.id).count()
        # Active load
        active = Fulfillment.query.filter(
            Fulfillment.stall_id == s.id,
            Fulfillment.status.in_(['ACCEPTED', 'PREPARING'])
        ).count()
        
        benchmarks.append({
            "stall_id": s.id,
            "name": s.name,
            "total_orders": total_orders,
            "current_active_load": active,
            "health_status": "CRITICAL" if active > 15 else "WARNING" if active > 10 else "HEALTHY"
        })
        
    return jsonify(success=True, benchmarks=benchmarks)


@intelligence_bp.route('/forecasts', methods=['GET'])
@require_auth
@require_tenant_role(['CANTEEN_MANAGER', 'ORG_ADMIN'])
def get_forecasts(current_user):
    from app.models.predictive import Forecast
    forecasts = Forecast.query.filter_by(status='ACTIVE').limit(50).all()
    return jsonify(success=True, forecasts=[{
        "product_id": f.product_id,
        "forecast_date": f.forecast_date.isoformat(),
        "predicted_quantity": f.predicted_quantity,
        "confidence": f.confidence,
        "model_version": f.model_version
    } for f in forecasts])

@intelligence_bp.route('/ask', methods=['POST'])
@require_auth
@require_tenant_role(['CANTEEN_MANAGER', 'ORG_ADMIN'])
def ask_intelligence(current_user):
    """
    Milestone 28: Natural Language Analytics (Read-Only)
    Milestone 101: Hallucination Control (Numeric Grounding)
    """
    data = request.get_json()
    question = data.get('question', '').lower()
    
    if not question:
        return jsonify(success=False, error={"code": "INVALID_QUERY", "message": "Question is required"}), 400
        
    # Safe Tool Selection (Milestone 134)
    # Map intents to our existing structured endpoints
    if "sell out" in question or "stockout" in question:
        from app.services.intelligence_service import IntelligenceService
        from app.models import IntelligenceSignal
        
        # Get actual grounded data
        signals = IntelligenceSignal.query.filter_by(status='OPEN', type='INVENTORY_ANOMALY').all()
        if not signals:
            return jsonify(success=True, answer="Currently, there are no items with a high probability of selling out.", data=[])
            
        names = [s.get_context().get('product_id') for s in signals] # In a real app we'd join with Product to get names
        return jsonify(success=True, answer=f"Based on current demand velocity, the following product IDs are at high risk of stockout: {', '.join(map(str, names))}.", data=[s.get_context() for s in signals])
        
    elif "prepare" in question or "waste" in question:
        from app.models import Recommendation
        recs = Recommendation.query.filter(Recommendation.type.in_(['INCREASE_PREPARATION', 'WASTE_MITIGATION']), Recommendation.status=='GENERATED').all()
        if not recs:
            return jsonify(success=True, answer="I do not have any preparation or waste recommendations at this time.", data=[])
            
        return jsonify(success=True, answer=f"I have {len(recs)} recommendations pending for preparation and waste. Please review the Recommendation Center.", data=[r.get_action() for r in recs])
        
    else:
        # Milestone 199: Unsupported Question / No Hallucination
        return jsonify(success=True, answer="Insufficient operational data to answer this reliably. I am currently trained to answer questions about stockouts, waste, and preparation recommendations.", data=[])
