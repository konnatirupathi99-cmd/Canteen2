import json
from app.services.agents.base_agent import BaseAgent, agent_tool
from app.models import Fulfillment, Stall
from app.extensions import db

class KitchenAgent(BaseAgent):
    """
    Milestone 9: Kitchen Agent
    Monitors kitchen load, bottlenecks, and generation of balancing recommendations.
    """
    def __init__(self):
        super().__init__()
        self.agent_id = 'KITCHEN_AGENT'
        self.agent_name = 'Kitchen Operations Agent'
        self.purpose = 'Monitor kitchen load and resolve prep bottlenecks'

    @agent_tool('get_kitchen_load', 'Fetches the current load for a specific kitchen stall', is_high_risk=False)
    def get_kitchen_load(self, task, stall_id):
        stall = Stall.query.get(stall_id)
        if not stall:
            return {"error": "Stall not found"}
            
        active_statuses = ['ACCEPTED', 'PREPARING']
        active_orders = Fulfillment.query.filter(
            Fulfillment.stall_id == stall_id,
            Fulfillment.status.in_(active_statuses)
        ).all()
        
        load = len(active_orders)
        capacity = stall.capacity or 20 # Mock default capacity
        
        return {
            "stall_name": stall.name,
            "current_load": load,
            "capacity": capacity,
            "is_overloaded": load >= capacity
        }

    def process_task(self, task):
        payload = task.input_payload
        action = payload.get('action')
        
        if action == 'CHECK_LOAD':
            stall_id = payload.get('stall_id')
            load_status = self.get_kitchen_load(task, stall_id)
            
            if load_status.get('is_overloaded'):
                return {
                    "result": "OVERLOADED",
                    "reason": f"Stall load ({load_status['current_load']}) exceeds capacity ({load_status['capacity']}).",
                    "recommendation": "Pause new orders for this stall or dispatch overflow."
                }
            return {
                "result": "HEALTHY",
                "reason": "Kitchen is operating within limits.",
                "evidence": load_status
            }
            
        raise ValueError(f"Unknown KitchenAgent action: {action}")
