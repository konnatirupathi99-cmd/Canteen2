from flask import Blueprint, jsonify, current_app
from ..extensions import db
from sqlalchemy import text

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """General health check endpoint for frontend dashboard."""
    db_status = "connected"
    try:
        db.session.execute(text('SELECT 1'))
    except Exception as e:
        current_app.logger.error(f"Health check - Database failed: {str(e)}")
        db_status = "disconnected"

    return jsonify({
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "service": "canteen-backend"
    }), 200

@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness: Is the process running?
    """
    return jsonify({
        "status": "alive",
        "service": "canteen-backend"
    }), 200

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness: Can the service safely receive traffic?
    Checks database connection and essential components.
    """
    dependencies = {
        "database": "unhealthy",
        "event_bus": "unhealthy" # Representing WebSocket/SocketIO availability
    }
    status = "healthy"
    status_code = 200

    try:
        db.session.execute(text('SELECT 1'))
        dependencies["database"] = "healthy"
    except Exception as e:
        current_app.logger.error(f"Readiness check - Database failed: {str(e)}")
        dependencies["database"] = "unhealthy"
        status = "unhealthy"
        status_code = 503

    # Event bus/WebSocket basic check
    # In a real setup, we might ping Redis or RabbitMQ. Here we assume healthy if app is up.
    dependencies["event_bus"] = "healthy"

    return jsonify({
        "status": status,
        "dependencies": dependencies
    }), status_code
