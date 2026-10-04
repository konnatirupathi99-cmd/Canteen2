import os
import logging
from flask import Flask, jsonify
from .config import config_by_name
from .extensions import db, migrate, cors, socketio

def setup_logging(app):
    """Configure structured logging."""
    logging.basicConfig(
        level=logging.INFO if not app.debug else logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.info("Logging initialized.")

def create_app(config_name=None):
    """Factory function to create the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    setup_logging(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models so Flask-Migrate can discover them
    from . import models
    
    # Configure CORS - explicitly allowing specific origins
    cors.init_app(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    
    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins=app.config['CORS_ORIGINS'])

    # Centralized Error Handling
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(success=False, error={"code": "BAD_REQUEST", "message": str(e.description)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(success=False, error={"code": "NOT_FOUND", "message": "The requested resource was not found."}), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        from flask import g
        correlation_id = getattr(g, 'correlation_id', 'unknown')
        app.logger.error(f"[{correlation_id}] Internal Server Error: {e}")
        return jsonify(success=False, error={"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."}), 500
    @app.before_request
    def set_correlation_id():
        from flask import request, g
        import uuid
        g.correlation_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        app.logger.info(f"[{g.correlation_id}] {request.method} {request.path}")

    @app.after_request
    def add_security_headers(response):
        from flask import g
        if hasattr(g, 'correlation_id'):
            response.headers['X-Correlation-ID'] = g.correlation_id
        # Security Hardening: Apply essential HTTP security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response

    # Register blueprints (routes)
    from .routes.health import health_bp
    from .routes.products import products_bp
    from .routes.orders import orders_bp
    from .routes.inventory import inventory_bp
    from .routes.analytics import analytics_bp
    from .routes.suppliers import suppliers_bp
    from .routes.procurement import procurement_bp
    from .routes.predictive import predictive_bp
    from .routes.central import central_bp
    from .routes.customer import customer_bp
    from .routes.intelligence import intelligence_bp
    from .routes.events import events_bp
    from .routes.twin import twin_bp
    from .routes.agents import agents_bp
    from .routes.automation import automation_bp
    from .routes.orchestration import orchestration_bp
    from .auth.routes import auth_bp
    
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(procurement_bp)
    app.register_blueprint(predictive_bp)
    app.register_blueprint(central_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(intelligence_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(twin_bp)
    app.register_blueprint(agents_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(orchestration_bp)
    app.register_blueprint(auth_bp)

    # Initialize agents (Milestone 2)
    with app.app_context():
        try:
            from .services.agents.orchestrator import AgentOrchestrator
            AgentOrchestrator.initialize_agents()
            app.logger.info("Operational Agents initialized.")
        except Exception as e:
            app.logger.error(f"Failed to initialize agents: {e}")

    # Register WebSocket events
    from .events import websocket_events # Ensure events are registered

    app.logger.info(f"Flask application created with config: {config_name}")
    return app
