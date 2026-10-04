import json
from app.services.agents.base_agent import BaseAgent, agent_tool
from app.models import Inventory, Product, GlobalProduct
from app.services.intelligence_service import IntelligenceService
from app.extensions import db

class InventoryAgent(BaseAgent):
    """
    Milestone 7: Inventory Agent
    Monitors inventory, detects low stock/imbalance, and recommends action.
    Cannot execute transfers/purchases directly.
    """
    def __init__(self):
        super().__init__()
        self.agent_id = 'INVENTORY_AGENT'
        self.agent_name = 'Inventory Operations Agent'
        self.purpose = 'Monitor inventory health and prevent stockouts'

    @agent_tool('get_inventory_status', 'Fetches current stock levels for a product', is_high_risk=False)
    def get_inventory_status(self, task, product_id):
        inv = Inventory.query.filter_by(product_id=product_id).first()
        if not inv:
            return {"error": "Inventory not found"}
        
        return {
            "quantity": inv.quantity,
            "low_stock_threshold": inv.low_stock_threshold,
            "is_critical": inv.quantity <= inv.low_stock_threshold
        }

    @agent_tool('create_restock_recommendation', 'Generates a recommendation to restock', is_high_risk=False)
    def create_restock_recommendation(self, task, product_id, reason, urgency):
        rec = IntelligenceService.create_recommendation(
            type='RESTOCK_RECOMMENDATION',
            reason=reason,
            suggested_action={"action": "flag_for_procurement", "product_id": product_id},
            priority=urgency,
            confidence=0.90,
            product_id=product_id
        )
        return {"recommendation_id": rec.id, "status": "CREATED"}

    def process_task(self, task):
        # Determine the action based on the trigger
        payload = task.input_payload
        action = payload.get('action')
        
        if action == 'CHECK_STOCKOUT_RISK':
            product_id = payload.get('product_id')
            
            # Use tools
            status = self.get_inventory_status(task, product_id)
            if "error" in status:
                return {"result": "IGNORED", "reason": "No inventory record"}
                
            if status['is_critical']:
                # The agent identifies a problem and decides to recommend action
                reason = f"Inventory is critically low ({status['quantity']} units left)."
                rec = self.create_restock_recommendation(task, product_id, reason, "HIGH")
                
                return {
                    "result": "RECOMMENDATION_GENERATED",
                    "reason": reason,
                    "evidence": status,
                    "action_taken": rec
                }
            else:
                return {
                    "result": "HEALTHY",
                    "reason": "Stock levels are above threshold",
                    "evidence": status
                }
                
        raise ValueError(f"Unknown InventoryAgent action: {action}")
