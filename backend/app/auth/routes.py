from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from app.models.user import User
from app.auth.middleware import generate_token, require_auth

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify(success=False, error={"code": "BAD_REQUEST", "message": "Email and password are required"}), 400

    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        if user.status != 'ACTIVE':
            return jsonify(success=False, error={"code": "FORBIDDEN", "message": "Account is not active"}), 403
            
        token = generate_token(user)
        return jsonify(
            success=True, 
            token=token,
            user={
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role
            }
        )
    
    return jsonify(success=False, error={"code": "UNAUTHORIZED", "message": "Invalid credentials"}), 401

@auth_bp.route('/me', methods=['GET'])
@require_auth
def current_user(current_user):
    return jsonify(
        success=True, 
        user={
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'role': current_user.role,
            'status': current_user.status
        }
    )
