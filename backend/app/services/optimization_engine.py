import logging
from app.extensions import db
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class OptimizationEngine:
    """
    Milestone 16: Optimization Engine
    Handles Resource Optimization, Multi-Objective Optimization, and Constraints.
    """
    
    @staticmethod
    def run_optimization(institution_id, objective_profile='BALANCED'):
        """
        Runs optimization across the given institution.
        Objective profiles: COST_FIRST, AVAILABILITY_FIRST, WASTE_MINIMIZATION, BALANCED
        Returns actionable recommendations.
        """
        # Get baseline snapshot
        from app.services.twin_service import DigitalTwinService
        snapshot = DigitalTwinService.generate_snapshot(institution_id, name=f"Optimization Baseline - {objective_profile}")
        state = snapshot.state_data
        
        recommendations = []
        
        # 1. Inventory Optimization (Milestone 18, 41)
        for product_id_str, inv_data in state.get('inventory', {}).items():
            product_id = int(product_id_str)
            qty = inv_data['quantity']
            low_stock = inv_data['low_stock_threshold']
            
            # For AVAILABILITY_FIRST, we keep stock high
            if objective_profile == 'AVAILABILITY_FIRST' and qty <= (low_stock * 1.5):
                recommendations.append({
                    "type": "GENERATE_REPLENISHMENT",
                    "context": {"product_id": product_id, "current_qty": qty, "reason": "Proactive replenishment for Availability First strategy."}
                })
                
            # For WASTE_MINIMIZATION, we run promotions if stock is > 2x low_stock
            if objective_profile == 'WASTE_MINIMIZATION' and qty > (low_stock * 2.0):
                recommendations.append({
                    "type": "WASTE_MITIGATION",
                    "context": {"product_id": product_id, "current_qty": qty, "reason": "Stock exceeds 200% of threshold. Recommend promotion."}
                })

        # 2. Kitchen/Stall Optimization (Milestone 19, 39, 40)
        stalls = state.get('stalls', {})
        active_orders = state.get('active_orders', {})
        
        overloaded_stalls = []
        underutilized_stalls = []
        
        for stall_id_str, stall_data in stalls.items():
            stall_id = int(stall_id_str)
            capacity = stall_data['capacity']
            load = active_orders.get(str(stall_id), 0)
            
            utilization = load / float(capacity) if capacity > 0 else 1.0
            
            if utilization > 1.2: # 120% utilized
                overloaded_stalls.append(stall_id)
            elif utilization < 0.5: # 50% utilized
                underutilized_stalls.append(stall_id)
                
        # If we have both, recommend load balancing (Milestone 39)
        if overloaded_stalls and underutilized_stalls:
            recommendations.append({
                "type": "STALL_LOAD_BALANCE",
                "context": {
                    "overloaded": overloaded_stalls, 
                    "underutilized": underutilized_stalls,
                    "reason": "Capacity imbalance detected across active stalls. Recommend dynamic menu routing."
                }
            })
            
        return recommendations
        
    @staticmethod
    def trigger_automated_policies(institution_id, recommendations):
        """
        Milestone 57: Automation Workflow Trigger
        Passes optimization recommendations into the Policy Engine for execution.
        """
        from app.services.automation_service import AutomationService
        
        execution_results = []
        for rec in recommendations:
            # Trigger event string matches the recommendation type
            trigger_event = rec['type']
            context_data = rec['context']
            
            # Evaluate against policies
            results = AutomationService.evaluate_and_execute(
                tenant_id=institution_id,
                trigger_event=trigger_event,
                context_data=context_data,
                dry_run=False
            )
            execution_results.extend(results)
            
        return execution_results
