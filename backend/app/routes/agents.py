from flask import Blueprint, jsonify, request
from app.auth.middleware import require_auth, require_tenant_role
from app.extensions import db
from app.models.agents import AgentRegistry, AgentTask, AgentToolExecution
from app.services.agents.orchestrator import AgentOrchestrator

agents_bp = Blueprint('agents', __name__, url_prefix='/api/v1/agents')

@agents_bp.route('/registry', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN'])
def get_agent_registry(current_user):
    agents = AgentRegistry.query.all()
    return jsonify(success=True, agents=[{
        "id": a.id,
        "name": a.name,
        "version": a.version,
        "purpose": a.purpose,
        "status": a.status,
        "failure_count": a.failure_count,
        "allowed_tools": a.allowed_tools,
        "last_execution_at": a.last_execution_at.isoformat() if a.last_execution_at else None
    } for a in agents])

@agents_bp.route('/<agent_id>/status', methods=['PUT'])
@require_auth
@require_tenant_role(['ORG_ADMIN'])
def set_agent_status(current_user, agent_id):
    """Milestone 53, 54: Agent Pause / Kill Switch"""
    status = request.json.get('status')
    if status not in ['ACTIVE', 'PAUSED', 'DISABLED']:
        return jsonify(success=False, error="Invalid status"), 400
        
    agent = AgentRegistry.query.get_or_404(agent_id)
    agent.status = status
    if status == 'ACTIVE':
        agent.failure_count = 0 # Manual recovery (Milestone 63)
        
    db.session.commit()
    return jsonify(success=True, agent_id=agent.id, new_status=agent.status)

@agents_bp.route('/tasks', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_agent_tasks(current_user):
    institution_id = request.args.get('institution_id')
    tasks = AgentTask.query.filter_by(institution_id=institution_id).order_by(AgentTask.created_at.desc()).limit(50).all()
    
    return jsonify(success=True, tasks=[{
        "id": t.id,
        "agent_id": t.agent_id,
        "trigger": t.trigger_event,
        "status": t.status,
        "priority": t.priority,
        "created_at": t.created_at.isoformat(),
        "completed_at": t.completed_at.isoformat() if t.completed_at else None
    } for t in tasks])

@agents_bp.route('/dispatch', methods=['POST'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def manual_dispatch(current_user):
    """Manually dispatch a task to an agent (for testing/override)."""
    data = request.get_json()
    institution_id = request.args.get('institution_id')
    
    task = AgentOrchestrator.dispatch_task(
        agent_id=data.get('agent_id'),
        trigger_event=data.get('trigger_event', 'MANUAL_DISPATCH'),
        payload=data.get('payload', {}),
        institution_id=institution_id
    )
    
    if not task:
        return jsonify(success=False, error="Dispatch failed"), 500
        
    return jsonify(success=True, task_id=task.id, status=task.status, result=task.result_payload)
