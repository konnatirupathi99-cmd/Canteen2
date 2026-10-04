from flask import Blueprint, jsonify, request
from app.auth.middleware import require_auth, require_tenant_role
from app.models import OutboxEvent
from app.extensions import db
from datetime import datetime, timezone

events_bp = Blueprint('events', __name__, url_prefix='/api/v1/events')

@events_bp.route('/failed', methods=['GET'])
@require_auth
@require_tenant_role(['SYSTEM_ADMIN', 'ORG_ADMIN'])
def get_failed_events(current_user):
    """
    Milestone 4/6: Event DLQ
    Returns events that have failed processing multiple times.
    """
    institution_id = request.args.get('institution_id')
    
    query = OutboxEvent.query.filter(
        OutboxEvent.processed == False,
        OutboxEvent.retry_count >= 3
    )
    if institution_id:
        query = query.filter_by(institution_id=institution_id)
        
    failed_events = query.order_by(OutboxEvent.created_at.desc()).limit(100).all()
    
    return jsonify(success=True, events=[{
        "id": e.id,
        "event_type": e.event_type,
        "aggregate_id": e.aggregate_id,
        "retry_count": e.retry_count,
        "error": e.error,
        "created_at": e.created_at.isoformat()
    } for e in failed_events])

@events_bp.route('/<event_id>/retry', methods=['POST'])
@require_auth
@require_tenant_role(['SYSTEM_ADMIN', 'ORG_ADMIN'])
def retry_event(current_user, event_id):
    """
    Milestone 4: Event Reprocessing
    Resets the retry counter and marks for reprocessing.
    """
    event = OutboxEvent.query.get(event_id)
    if not event:
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "Event not found"}), 404
        
    institution_id = request.args.get('institution_id') or (request.is_json and request.json.get('institution_id'))
    if institution_id and str(event.institution_id) != str(institution_id):
        return jsonify(success=False, error={"code": "FORBIDDEN", "message": "Not your event"}), 403
        
    event.retry_count = 0
    event.error = None
    event.processed = False
    
    db.session.commit()
    
    # In a real architecture, we would immediately dispatch it or rely on the background worker
    return jsonify(success=True, message="Event queued for retry")

@events_bp.route('/<event_id>/discard', methods=['POST'])
@require_auth
@require_tenant_role(['SYSTEM_ADMIN', 'ORG_ADMIN'])
def discard_event(current_user, event_id):
    """
    Milestone 4: DLQ Discard
    Marks the event as processed to ignore it.
    """
    event = OutboxEvent.query.get(event_id)
    if not event:
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "Event not found"}), 404
        
    event.processed = True
    event.processed_at = datetime.now(timezone.utc)
    event.error = event.error + " (DISCARDED BY ADMIN)" if event.error else "(DISCARDED BY ADMIN)"
    
    db.session.commit()
    
    return jsonify(success=True, message="Event discarded")
