import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-prod')
    JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-jwt-secret')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///canteen.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Phase 22 Database Resilience
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True, # Connection Health Check
        "pool_recycle": 300,   # Avoid stale connections
        "pool_timeout": 10,    # Circuit break DB if unavailable
    }
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'sqlite:///test.db')

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
# Config dictionary for easy selection
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
