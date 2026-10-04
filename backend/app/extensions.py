from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO

# Initialize extensions without binding to app yet
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
socketio = SocketIO()
