from flask import Blueprint, jsonify, request, g
from app.extensions import db
from app.auth.middleware import require_auth, require_tenant_role
from app.models.automation import AutomationPolicy, AutomationExecution
from app.models.twin import OperationalSnapshot, SimulationScenario, SimulationResult
from app.services.automation_service import AutomationService
from app.services.optimization_engine import OptimizationEngine

automation_bp = Blueprint('automation', __name__, url_prefix='/api/v1/automation')

@automation_bp.route('/policies', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'SYSTEM_ADMIN'])
def get_policies(current_user):
    tenant_id = request.args.get('tenant_id', g.tenant_id)
    policies = AutomationPolicy.query.filter_by(tenant_id=tenant_id).all()
    
    return jsonify({
        "success": True,
        "policies": [{
            "id": p.id,
            "name": p.name,
            "trigger": p.trigger_event,
            "conditions": p.get_conditions(),
            "action": p.action_type,
            "autonomy_level": p.autonomy_level,
            "status": p.status,
            "cooldown_minutes": p.cooldown_minutes
        } for p in policies]
    })

@automation_bp.route('/policies', methods=['POST'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'SYSTEM_ADMIN'])
def create_policy(current_user):
    data = request.json
    
    import json
    policy = AutomationPolicy(
        tenant_id=g.tenant_id,
        name=data.get('name'),
        description=data.get('description'),
        trigger_event=data.get('trigger_event'),
        conditions=json.dumps(data.get('conditions', {})),
        action_type=data.get('action_type'),
        autonomy_level=data.get('autonomy_level', 'LEVEL_3'),
        limits=json.dumps(data.get('limits', {})),
        cooldown_minutes=data.get('cooldown_minutes', 60),
        status=data.get('status', 'DRAFT'),
        created_by=current_user.id
    )
    
    db.session.add(policy)
    db.session.commit()
    return jsonify({"success": True, "policy_id": policy.id}), 201

@automation_bp.route('/policies/<policy_id>/status', methods=['PUT'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'SYSTEM_ADMIN'])
def update_policy_status(current_user, policy_id):
    """
    Milestone 15, 32, 100: Kill Switch and Policy State Management
    """
    status = request.json.get('status')
    if status not in ['DRAFT', 'TESTING', 'ACTIVE', 'PAUSED', 'DEPRECATED', 'ARCHIVED']:
        return jsonify({"success": False, "error": "Invalid status"}), 400
        
    policy = AutomationPolicy.query.get_or_404(policy_id)
    
    # Enforce Tenant Isolation
    if policy.tenant_id != g.tenant_id and current_user.role != 'SYSTEM_ADMIN':
        return jsonify({"success": False, "error": "Forbidden"}), 403
        
    policy.status = status
    db.session.commit()
    
    return jsonify({"success": True, "message": f"Policy updated to {status}"})

@automation_bp.route('/executions', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_executions(current_user):
    """
    Milestone 157: Governance Dashboard (Audit trail of executions)
    """
    executions = AutomationExecution.query.filter_by(tenant_id=g.tenant_id)\
                                        .order_by(AutomationExecution.executed_at.desc())\
                                        .limit(50).all()
                                        
    return jsonify({
        "success": True,
        "executions": [{
            "id": e.id,
            "policy_id": e.policy_id,
            "trigger_event": e.trigger_event,
            "action_type": e.action_type,
            "status": e.status,
            "reason": e.reason,
            "executed_at": e.executed_at.isoformat()
        } for e in executions]
    })

@automation_bp.route('/simulate', methods=['POST'])
@require_auth
@require_tenant_role(['ORG_ADMIN'])
def trigger_simulation(current_user):
    """
    Milestone 9: Policy Simulation / What-If Engine
    """
    data = request.json
    scenario_type = data.get('scenario_type')
    parameters = data.get('parameters', {})
    
    from app.services.twin_service import DigitalTwinService
    from app.services.simulation_engine import SimulationEngine
    
    # 1. Take baseline snapshot
    snapshot = DigitalTwinService.generate_snapshot(g.tenant_id, name="API-Triggered Simulation Baseline")
    
    # 2. Create Scenario
    scenario = SimulationScenario(
        institution_id=g.tenant_id,
        name=data.get('name', f"Simulation - {scenario_type}"),
        scenario_type=scenario_type,
        base_snapshot_id=snapshot.id,
        parameters=parameters,
        created_by=current_user.id
    )
    db.session.add(scenario)
    db.session.commit()
    
    # 3. Run Engine
    result = SimulationEngine.run_scenario(scenario)
    
    return jsonify({
        "success": True,
        "scenario_id": scenario.id,
        "result_id": result.id,
        "risks_detected": result.result_data.get('risks_detected', []),
        "confidence_score": result.confidence_score
    })

@automation_bp.route('/optimize', methods=['POST'])
@require_auth
@require_tenant_role(['ORG_ADMIN'])
def trigger_optimization(current_user):
    """
    Milestone 16, 57: Trigger Optimization Engine and execute automated policies
    """
    strategy = request.json.get('strategy', 'BALANCED')
    
    # 1. Run Optimization Engine to get recommendations
    recommendations = OptimizationEngine.run_optimization(g.tenant_id, strategy)
    
    # 2. Feed recommendations into Policy Engine
    # If a policy is ACTIVE and matches the constraints, it will execute (or generate approval request)
    exec_results = OptimizationEngine.trigger_automated_policies(g.tenant_id, recommendations)
    
    return jsonify({
        "success": True,
        "strategy": strategy,
        "recommendations_generated": len(recommendations),
        "policy_execution_results": exec_results
    })
