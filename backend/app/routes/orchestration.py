from flask import Blueprint, jsonify, request, g
from app.extensions import db
from app.auth.middleware import require_auth, require_tenant_role
from app.models.orchestration import OperationalIncident, Workflow, WorkflowStep, DigitalTwinHealth
import json

orchestration_bp = Blueprint('orchestration', __name__, url_prefix='/api/v1/orchestration')

@orchestration_bp.route('/incidents', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_incidents(current_user):
    """
    MILESTONE 14: Incident Management
    Retrieves the operator task queue of incidents.
    """
    tenant_id = request.args.get('tenant_id', g.tenant_id)
    status = request.args.get('status', 'OPEN')
    
    incidents = OperationalIncident.query.filter_by(tenant_id=tenant_id, status=status).order_by(OperationalIncident.detected_at.desc()).all()
    
    return jsonify({
        "success": True,
        "incidents": [{
            "id": i.id,
            "title": i.title,
            "severity": i.severity,
            "anomaly_type": i.anomaly_type,
            "affected_service": i.affected_service,
            "status": i.status,
            "detected_at": i.detected_at.isoformat() if i.detected_at else None,
            "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
            "workflow_id": i.workflow_id
        } for i in incidents]
    })

@orchestration_bp.route('/workflows', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'SYSTEM_ADMIN'])
def get_workflows(current_user):
    """
    MILESTONE 27: Control Room - Workflow visibility
    """
    tenant_id = request.args.get('tenant_id', g.tenant_id)
    workflows = Workflow.query.filter_by(tenant_id=tenant_id).order_by(Workflow.created_at.desc()).limit(50).all()
    
    return jsonify({
        "success": True,
        "workflows": [{
            "id": w.id,
            "name": w.name,
            "status": w.status,
            "created_at": w.created_at.isoformat() if w.created_at else None,
            "completed_at": w.completed_at.isoformat() if w.completed_at else None,
            "correlation_id": w.correlation_id,
            "steps": len(w.steps)
        } for w in workflows]
    })

@orchestration_bp.route('/twin-health', methods=['GET'])
@require_auth
@require_tenant_role(['ORG_ADMIN', 'CANTEEN_MANAGER'])
def get_twin_health(current_user):
    """
    MILESTONE 8, 27: Digital Twin Comparison / Health Dashboard
    """
    tenant_id = request.args.get('tenant_id', g.tenant_id)
    health = DigitalTwinHealth.query.filter_by(tenant_id=tenant_id).first()
    
    if not health:
        return jsonify({"success": True, "health": {"status": "UNKNOWN"}})
        
    return jsonify({
        "success": True,
        "health": {
            "status": health.status,
            "state_divergence_score": health.state_divergence_score,
            "event_lag_ms": health.event_lag_ms,
            "last_synced_at": health.last_synced_at.isoformat() if health.last_synced_at else None,
            "last_reconciliation_at": health.last_reconciliation_at.isoformat() if health.last_reconciliation_at else None
        }
    })

@orchestration_bp.route('/twin-health/reconcile', methods=['POST'])
@require_auth
@require_tenant_role(['ORG_ADMIN'])
def reconcile_twin(current_user):
    """
    MILESTONE 9, 25: Manual trigger for twin reconciliation.
    """
    from app.services.twin_sync import DigitalTwinSyncService
    success = DigitalTwinSyncService.reconcile(g.tenant_id)
    
    return jsonify({
        "success": success,
        "message": "Reconciliation completed" if success else "Failed to reconcile"
    })
