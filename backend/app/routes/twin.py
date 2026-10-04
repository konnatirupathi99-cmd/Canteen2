from flask import Blueprint, jsonify, request
from app.auth.middleware import require_auth, require_tenant_role
from app.extensions import db
from app.models.twin import OperationalSnapshot, SimulationScenario, SimulationResult, OperationalRisk
from app.services.twin_service import DigitalTwinService
from app.services.simulation_engine import SimulationEngine

twin_bp = Blueprint('twin', __name__, url_prefix='/api/v1/twin')

# ==========================================
# MILESTONE 3 & 4: Snapshots & Sync
# ==========================================
@twin_bp.route('/snapshots/current', methods=['POST'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def create_snapshot(current_user):
    institution_id = request.args.get('institution_id')
    name = request.json.get('name') if request.is_json else None
    
    snapshot = DigitalTwinService.generate_snapshot(institution_id, name)
    
    return jsonify(success=True, snapshot_id=snapshot.id, timestamp=snapshot.timestamp.isoformat()), 201

@twin_bp.route('/snapshots', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def list_snapshots(current_user):
    institution_id = request.args.get('institution_id')
    snapshots = OperationalSnapshot.query.filter_by(institution_id=institution_id).order_by(OperationalSnapshot.timestamp.desc()).limit(20).all()
    
    return jsonify(success=True, snapshots=[{
        "id": s.id,
        "name": s.name,
        "timestamp": s.timestamp.isoformat(),
        "version": s.version
    } for s in snapshots])

# ==========================================
# MILESTONE 5 & 6: Simulation & Scenarios
# ==========================================
@twin_bp.route('/scenarios', methods=['POST'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def create_and_run_scenario(current_user):
    data = request.get_json()
    institution_id = request.args.get('institution_id')
    
    base_snapshot_id = data.get('base_snapshot_id')
    if not base_snapshot_id:
        # Auto-generate a fresh snapshot if none provided
        snap = DigitalTwinService.generate_snapshot(institution_id)
        base_snapshot_id = snap.id
        
    scenario = SimulationScenario(
        institution_id=institution_id,
        name=data.get('name', 'Untitled Scenario'),
        scenario_type=data.get('scenario_type'),
        base_snapshot_id=base_snapshot_id,
        parameters=data.get('parameters', {}),
        created_by=current_user.id
    )
    db.session.add(scenario)
    db.session.commit()
    
    # Milestone 22: Async in production, synchronous here for MVP API response
    result = SimulationEngine.run_scenario(scenario)
    
    return jsonify(success=True, scenario_id=scenario.id, result_id=result.id), 201

@twin_bp.route('/results/<int:result_id>', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_simulation_result(current_user, result_id):
    result = SimulationResult.query.get_or_404(result_id)
    return jsonify(success=True, result={
        "id": result.id,
        "scenario_id": result.scenario_id,
        "status": result.status,
        "confidence_score": result.confidence_score,
        "violations": result.constraint_violations,
        "data": result.result_data,
        "created_at": result.created_at.isoformat()
    })

# ==========================================
# MILESTONE 7: Scenario Comparison
# ==========================================
@twin_bp.route('/compare', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def compare_scenarios(current_user):
    result_a_id = request.args.get('result_a')
    result_b_id = request.args.get('result_b')
    
    if not result_a_id or not result_b_id:
        return jsonify(success=False, error="Requires result_a and result_b"), 400
        
    res_a = SimulationResult.query.get_or_404(result_a_id)
    res_b = SimulationResult.query.get_or_404(result_b_id)
    
    # Simplified diff based on detected risks
    diff = {
        "scenario_a_risks": len(res_a.result_data.get('risks_detected', [])),
        "scenario_b_risks": len(res_b.result_data.get('risks_detected', [])),
        "a_confidence": res_a.confidence_score,
        "b_confidence": res_b.confidence_score
    }
    
    return jsonify(success=True, comparison=diff)

# ==========================================
# MILESTONE 13: Risk Center
# ==========================================
@twin_bp.route('/risks', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_operational_risks(current_user):
    institution_id = request.args.get('institution_id')
    risks = OperationalRisk.query.filter_by(
        institution_id=institution_id,
        status='ACTIVE'
    ).order_by(OperationalRisk.impact_score.desc()).all()
    
    return jsonify(success=True, risks=[{
        "id": r.id,
        "type": r.risk_type,
        "title": r.title,
        "probability": r.probability,
        "impact": r.impact_score,
        "urgency": r.urgency,
        "created_at": r.created_at.isoformat()
    } for r in risks])

# ==========================================
# MILESTONE 14: Playbooks
# ==========================================
from app.models.twin import OperationalPlaybook

@twin_bp.route('/playbooks', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_playbooks(current_user):
    institution_id = request.args.get('institution_id')
    playbooks = OperationalPlaybook.query.filter_by(institution_id=institution_id).all()
    
    return jsonify(success=True, playbooks=[{
        "id": p.id,
        "name": p.name,
        "trigger": p.trigger_condition,
        "steps": p.playbook_steps
    } for p in playbooks])
