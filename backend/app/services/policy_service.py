from app.models.policy import Policy
from app.models.organization import Stall, Canteen, Campus

class PolicyService:
    @staticmethod
    def resolve_policy(policy_key, stall_id=None, canteen_id=None, campus_id=None, institution_id=None, default_val=None):
        """
        Resolves a policy value by traversing up the organizational hierarchy.
        Most specific overrides least specific.
        """
        # Resolve higher level IDs if not provided
        if stall_id and not canteen_id:
            stall = Stall.query.get(stall_id)
            if stall: canteen_id = stall.canteen_id
            
        if canteen_id and not campus_id:
            canteen = Canteen.query.get(canteen_id)
            if canteen: campus_id = canteen.campus_id
            
        if campus_id and not institution_id:
            campus = Campus.query.get(campus_id)
            if campus: institution_id = campus.institution_id

        # 1. Stall Level
        if stall_id:
            p = Policy.query.filter_by(stall_id=stall_id, policy_key=policy_key).first()
            if p: return p.policy_value
            
        # 2. Canteen Level
        if canteen_id:
            p = Policy.query.filter_by(canteen_id=canteen_id, policy_key=policy_key).first()
            if p: return p.policy_value
            
        # 3. Campus Level
        if campus_id:
            p = Policy.query.filter_by(campus_id=campus_id, policy_key=policy_key).first()
            if p: return p.policy_value
            
        # 4. Institution Level
        if institution_id:
            p = Policy.query.filter_by(institution_id=institution_id, policy_key=policy_key).first()
            if p: return p.policy_value
            
        # 5. System Default
        p = Policy.query.filter_by(stall_id=None, canteen_id=None, campus_id=None, institution_id=None, policy_key=policy_key).first()
        if p: return p.policy_value
        
        return default_val

    @staticmethod
    def requires_approval(action_type, amount, institution_id=None):
        """
        Evaluates approval policies for operations like Purchase Requests, Refunds, or Adjustments.
        Returns: (bool requires_approval, str reason)
        """
        # Example policy_key: MAX_AUTO_PURCHASE
        if action_type == 'PURCHASE':
            limit = PolicyService.resolve_policy('MAX_AUTO_PURCHASE', institution_id=institution_id, default_val='500')
            if float(amount) > float(limit):
                return True, f"Purchase amount ({amount}) exceeds automatic approval limit ({limit})"
                
        elif action_type == 'INVENTORY_ADJUSTMENT':
            limit = PolicyService.resolve_policy('MAX_AUTO_ADJUSTMENT_VALUE', institution_id=institution_id, default_val='100')
            if float(amount) > float(limit):
                return True, f"Adjustment value ({amount}) exceeds automatic approval limit ({limit})"
                
        return False, "Within policy limits"
