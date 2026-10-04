import jwt
from functools import wraps
from flask import request, jsonify, current_app, g
from app.models.user import User

def generate_token(user):
    payload = {
        'sub': str(user.id),
        'role': user.role,
        'status': user.status,
        'org': str(user.organization_id) if user.organization_id else None
    }
    # For MVP, we use a simple encoding. In production add 'exp'
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
                
        if not token:
            return jsonify(success=False, error={"code": "UNAUTHORIZED", "message": "Missing authentication token"}), 401
            
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['sub'])
            
            if not current_user or current_user.status != 'ACTIVE':
                return jsonify(success=False, error={"code": "UNAUTHORIZED", "message": "User inactive or not found"}), 401
            
            # Centralized Tenant Context
            g.tenant_id = current_user.organization_id
                
        except jwt.ExpiredSignatureError:
            return jsonify(success=False, error={"code": "UNAUTHORIZED", "message": "Token expired"}), 401
        except jwt.InvalidTokenError as e:
            print("INVALID TOKEN ERROR:", str(e))
            return jsonify(success=False, error={"code": "UNAUTHORIZED", "message": "Invalid token"}), 401
            
        # Inject the current user into the kwargs
        return f(current_user=current_user, *args, **kwargs)
    return decorated

def require_role(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify(success=False, error={"code": "FORBIDDEN", "message": "You do not have permission to access this resource"}), 403
            return f(current_user=current_user, *args, **kwargs)
        return decorated_function
    return decorator

def require_tenant_role(allowed_roles):
    """
    Checks if the user has one of the allowed_roles in the context of the current institution.
    For this MVP transition, we check OrganizationMembership or the global role if the user is a system admin.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role == 'SYSTEM_ADMIN':
                return f(current_user=current_user, *args, **kwargs)
                
            institution_id = request.view_args.get('institution_id') or request.args.get('institution_id')
            if not institution_id and request.is_json:
                institution_id = request.json.get('institution_id')
                
            if not institution_id:
                # If no explicit institution_id is provided, check if the global role is sufficient (backward compatibility for non-tenant aware routes)
                if current_user.role in allowed_roles:
                     return f(current_user=current_user, *args, **kwargs)
                return jsonify(success=False, error={"code": "FORBIDDEN", "message": "Tenant context required or insufficient permissions"}), 403

            # Check organization membership
            from app.models.organization import OrganizationMembership
            membership = OrganizationMembership.query.filter_by(
                user_id=current_user.id, 
                institution_id=institution_id
            ).first()
            
            if membership and membership.role in allowed_roles:
                return f(current_user=current_user, *args, **kwargs)
                
            # Fallback for hackathon transition: if they have the global role and are tied to the institution via User.institution_id
            if current_user.role in allowed_roles and str(current_user.institution_id) == str(institution_id):
                return f(current_user=current_user, *args, **kwargs)
                
            return jsonify(success=False, error={"code": "FORBIDDEN", "message": "You do not have permission in this institution"}), 403
        return decorated_function
    return decorator
