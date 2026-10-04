from flask_socketio import emit
from ..extensions import socketio
from flask import request
import logging

logger = logging.getLogger(__name__)

@socketio.on('connect')
def handle_connect():
    """Event triggered when a new client connects to the WebSocket."""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected', 'message': 'Successfully connected to backend WebSocket.'})

@socketio.on('disconnect')
def handle_disconnect():
    """Event triggered when a client disconnects."""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('test_event')
def handle_test_event(data):
    """
    Test event to verify bidirectional communication.
    """
    logger.info(f"Received test_event from {request.sid}: {data}")
    emit('test_response', {'message': 'pong', 'received': data})

@socketio.on('request_kds_state')
def handle_request_kds_state(data):
    """
    Phase 13 Resilience: State Reconciliation for KDS offline mode.
    When KDS reconnects, it queries current server state.
    """
    stall_id = data.get('stall_id')
    if not stall_id:
        emit('kds_state_error', {'message': 'stall_id required'})
        return
        
    from ..models.order import Fulfillment
    
    # Synchronize CONFIRMED, ACCEPTED, PREPARING, READY orders
    active_statuses = ['CONFIRMED', 'ACCEPTED', 'PREPARING', 'READY']
    active_fulfillments = Fulfillment.query.filter(
        Fulfillment.stall_id == stall_id,
        Fulfillment.status.in_(active_statuses)
    ).all()
    
    result = []
    for f in active_fulfillments:
        result.append({
            "fulfillment_id": f.id,
            "order_id": f.order_id,
            "status": f.status,
            "updated_at": f.updated_at.isoformat() if f.updated_at else None
        })
        
    logger.info(f"KDS Reconnected for Stall {stall_id}. Sent {len(result)} active fulfillments.")
    emit('kds_state_response', {'stall_id': stall_id, 'active_orders': result})
