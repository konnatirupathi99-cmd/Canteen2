import json
from app.services.agents.base_agent import BaseAgent, agent_tool
from app.services.federation_service import FederationService
from app.extensions import db

class EnterpriseAgent(BaseAgent):
    """
    Milestone 11 & 12: Enterprise Agent & Delegation
    Operates at the enterprise scope, coordinating actions across multiple campuses.
    """
    def __init__(self):
        super().__init__()
        self.agent_id = 'ENTERPRISE_AGENT'
        self.agent_name = 'Enterprise Operations Agent'
        self.purpose = 'Coordinate cross-campus operations and policies'
        self.scope = 'ENTERPRISE'

    @agent_tool('request_campus_transfer', 'Requests a stock transfer between two campuses', is_high_risk=True)
    def request_campus_transfer(self, task, source_canteen_id, target_canteen_id, product_id, quantity):
        """Milestone 14: Inventory transfer workflow"""
        # Publish the federated event
        event_id = FederationService.publish_federated_event(
            institution_id=task.institution_id,
            campus_id=target_canteen_id,
            event_type='TRANSFER_REQUESTED',
            payload={
                "source_canteen_id": source_canteen_id,
                "target_canteen_id": target_canteen_id,
                "product_id": product_id,
                "quantity": quantity,
                "status": "PENDING_APPROVAL" # Policy check
            }
        )
        return {"federated_event_id": event_id, "status": "PENDING_APPROVAL"}

    def process_task(self, task):
        payload = task.input_payload
        action = payload.get('action')
        
        if action == 'RESOLVE_NETWORK_STOCKOUT':
            product_id = payload.get('product_id')
            target_canteen_id = payload.get('canteen_id')
            needed_quantity = payload.get('needed_quantity', 50)
            
            # Step 1: Detect imbalance (Milestone 13)
            surplus = FederationService.detect_network_inventory_imbalance(
                institution_id=task.institution_id,
                product_id=product_id,
                needed_quantity=needed_quantity
            )
            
            if surplus:
                # Step 2: Recommend/Request transfer
                result = self.request_campus_transfer(
                    task, 
                    source_canteen_id=surplus['source_canteen_id'],
                    target_canteen_id=target_canteen_id,
                    product_id=product_id,
                    quantity=needed_quantity
                )
                
                return {
                    "result": "TRANSFER_RECOMMENDED",
                    "reason": f"Found surplus at canteen {surplus['source_canteen_id']}.",
                    "action_taken": result
                }
            else:
                return {
                    "result": "NO_SURPLUS_FOUND",
                    "reason": "No local canteen has enough surplus to cover the stockout.",
                    "recommend_action": {
                        "agent": "PROCUREMENT_AGENT",
                        "action": "PROCESS_RESTOCK_RECOMMENDATION",
                        "product_id": product_id,
                        "quantity": needed_quantity * 2
                    }
                }
                
        raise ValueError(f"Unknown EnterpriseAgent action: {action}")
