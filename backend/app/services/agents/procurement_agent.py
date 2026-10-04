import json
from app.services.agents.base_agent import BaseAgent, agent_tool
from app.models.procurement import PurchaseRequest
from app.models.supplier import Supplier
from app.extensions import db

class ProcurementAgent(BaseAgent):
    """
    Milestone 10: Procurement Agent
    Monitors purchasing requirements and supplier reliability.
    """
    def __init__(self):
        super().__init__()
        self.agent_id = 'PROCUREMENT_AGENT'
        self.agent_name = 'Procurement & Supplier Agent'
        self.purpose = 'Manage restock requests and supplier risk'

    @agent_tool('create_purchase_draft', 'Creates a draft purchase request based on inventory needs', is_high_risk=True)
    def create_purchase_draft(self, task, supplier_id, product_id, quantity, expected_cost):
        pr = PurchaseRequest(
            institution_id=task.institution_id,
            supplier_id=supplier_id,
            total_amount=expected_cost,
            status='DRAFT', # High-risk actions require HUMAN APPROVAL
            items=[{
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": expected_cost / quantity
            }]
        )
        db.session.add(pr)
        db.session.commit()
        return {"purchase_request_id": pr.id, "status": "DRAFT_CREATED"}

    def process_task(self, task):
        payload = task.input_payload
        action = payload.get('action')
        
        if action == 'PROCESS_RESTOCK_RECOMMENDATION':
            product_id = payload.get('product_id')
            supplier_id = payload.get('supplier_id')
            quantity = payload.get('quantity', 100)
            expected_cost = payload.get('expected_cost', 0)
            
            # Policy Engine check: Does the agent have the authority? 
            # Handled inherently by `is_high_risk=True` pushing it to DRAFT status
            result = self.create_purchase_draft(task, supplier_id, product_id, quantity, expected_cost)
            
            return {
                "result": "DRAFT_CREATED",
                "reason": f"Drafted PR for {quantity} units. Awaiting manager approval.",
                "action_taken": result
            }
            
        raise ValueError(f"Unknown ProcurementAgent action: {action}")
