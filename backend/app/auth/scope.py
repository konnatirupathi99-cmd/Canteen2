from app.models.organization import OrganizationMembership, Canteen, Campus, Institution
from app.models.stall import Stall

def has_scope_permission(user, required_roles, institution_id=None, campus_id=None, canteen_id=None, stall_id=None):
    """
    Checks if a user has any of the required_roles at or above the specified organizational scope.
    """
    if user.role in ['SYSTEM_ADMIN']:
        return True
        
    # Check if they have an explicit OrganizationMembership that covers this scope
    memberships = OrganizationMembership.query.filter_by(user_id=user.id).all()
    
    # Map out the exact hierarchy of the requested resource if not provided fully
    # (e.g. if only stall_id is provided, resolve canteen, campus, institution)
    req_inst = institution_id
    req_camp = campus_id
    req_cant = canteen_id
    req_stall = stall_id
    
    if req_stall and not req_cant:
        stall = Stall.query.get(req_stall)
        if stall: req_cant = stall.canteen_id
    if req_cant and not req_camp:
        canteen = Canteen.query.get(req_cant)
        if canteen: req_camp = canteen.campus_id
    if req_camp and not req_inst:
        campus = Campus.query.get(req_camp)
        if campus: req_inst = campus.institution_id
        
    # If no specific scope is requested, just check if they have the role at all
    has_specific_request = any([req_inst, req_camp, req_cant, req_stall])
        
    for m in memberships:
        if m.role not in required_roles and m.role != 'SYSTEM_ADMIN':
            continue
            
        if not has_specific_request:
            return True
            
        # Does this membership cover the requested scope?
        if m.institution_id:
            if m.institution_id == req_inst:
                return True
        elif m.campus_id:
            if m.campus_id == req_camp:
                return True
        elif m.canteen_id:
            if m.canteen_id == req_cant:
                return True
        elif m.stall_id:
            if m.stall_id == req_stall:
                return True

    # Fallback for legacy (pre-Phase 11) data
    if not memberships and user.role in required_roles:
        if user.role == 'ADMIN': # ADMIN acts as Institution Admin for legacy
            return True
        if user.role == 'CANTEEN_MANAGER':
            return True # Legacy canteen manager could access anything
        if user.role in ['KITCHEN_STAFF', 'STALL_MANAGER']:
            if not req_stall or user.stall_id == req_stall:
                return True

    return False

def get_authorized_canteen_ids(user):
    """Returns a list of canteen IDs the user is authorized to view."""
    if user.role in ['SYSTEM_ADMIN', 'ADMIN']:
        return [c.id for c in Canteen.query.all()]
        
    memberships = OrganizationMembership.query.filter_by(user_id=user.id).all()
    authorized = set()
    for m in memberships:
        if m.institution_id:
            for camp in Campus.query.filter_by(institution_id=m.institution_id).all():
                for cant in Canteen.query.filter_by(campus_id=camp.id).all():
                    authorized.add(cant.id)
        elif m.campus_id:
            for cant in Canteen.query.filter_by(campus_id=m.campus_id).all():
                authorized.add(cant.id)
        elif m.canteen_id:
            authorized.add(m.canteen_id)
            
    # Legacy fallback
    if not memberships and user.role == 'CANTEEN_MANAGER':
        for cant in Canteen.query.all():
            authorized.add(cant.id)
            
    return list(authorized)

def get_authorized_campus_ids(user):
    if user.role in ['SYSTEM_ADMIN', 'ADMIN']:
        return [c.id for c in Campus.query.all()]
    
    memberships = OrganizationMembership.query.filter_by(user_id=user.id).all()
    authorized = set()
    for m in memberships:
        if m.institution_id:
            for camp in Campus.query.filter_by(institution_id=m.institution_id).all():
                authorized.add(camp.id)
        elif m.campus_id:
            authorized.add(m.campus_id)
            
    return list(authorized)
