import json
import copy
from datetime import datetime, timezone
from app.extensions import db
from app.models.twin import SimulationResult, OperationalRisk

class SimulationEngine:
    @staticmethod
    def run_scenario(scenario):
        """
        Milestones 5, 6, 11: Scenario Engine & What-If Simulation
        Runs entirely on isolated state (copied from snapshot).
        Does not mutate production DB.
        """
        # 1. Load the baseline state from the Snapshot
        baseline_state = copy.deepcopy(scenario.snapshot.state_data)
        simulated_state = copy.deepcopy(baseline_state)
        
        parameters = scenario.parameters
        scenario_type = scenario.scenario_type
        
        violations = []
        risks_detected = []
        
        # 2. Apply Scenario Mutations
        if scenario_type == 'DEMAND_SURGE':
            # Parameters: {"product_id": 1, "multiplier": 1.5}
            product_id = str(parameters.get('product_id'))
            multiplier = float(parameters.get('multiplier', 1.0))
            
            # Simulate the effect on inventory (assume base hourly demand of 10 for MVP simulation)
            base_hourly_demand = 10 
            simulated_demand = base_hourly_demand * multiplier
            
            if product_id in simulated_state['inventory']:
                inv = simulated_state['inventory'][product_id]
                hours_to_stockout = inv['quantity'] / max(simulated_demand, 1)
                
                simulated_state['inventory'][product_id]['projected_hours_to_stockout'] = hours_to_stockout
                
                # Check constraints
                if hours_to_stockout < 2:
                    risks_detected.append({
                        "type": "STOCKOUT_RISK",
                        "impact": "HIGH",
                        "message": f"Demand surge will deplete inventory in {round(hours_to_stockout, 1)} hours."
                    })
            else:
                violations.append("Product not found in inventory snapshot.")
                
        elif scenario_type == 'STAFF_SHORTAGE':
            # Parameters: {"stall_id": 1, "capacity_reduction": 0.5}
            stall_id = str(parameters.get('stall_id'))
            reduction = float(parameters.get('capacity_reduction', 0.5))
            
            if stall_id in simulated_state['stalls']:
                current_capacity = simulated_state['stalls'][stall_id]['capacity']
                new_capacity = current_capacity * (1 - reduction)
                simulated_state['stalls'][stall_id]['capacity'] = new_capacity
                
                active_orders = simulated_state['active_orders'].get(stall_id, 0)
                
                if active_orders > new_capacity:
                    risks_detected.append({
                        "type": "KITCHEN_BOTTLENECK",
                        "impact": "CRITICAL",
                        "message": f"Reduced capacity ({new_capacity}) cannot handle active load ({active_orders})."
                    })
            else:
                violations.append("Stall not found in snapshot.")
                
        elif scenario_type == 'SUPPLIER_DELAY':
            # Parameters: {"supplier_id": 1, "delay_hours": 24}
            supplier_id = int(parameters.get('supplier_id'))
            delay = int(parameters.get('delay_hours', 24))
            
            # Adjust lead times in the twin
            affected_products = 0
            for pid, suppliers in simulated_state['suppliers'].items():
                for s in suppliers:
                    if s['supplier_id'] == supplier_id:
                        s['lead_time_hours'] += delay
                        affected_products += 1
                        
            if affected_products > 0:
                risks_detected.append({
                    "type": "SUPPLY_CHAIN_DELAY",
                    "impact": "MEDIUM",
                    "message": f"Supplier delay affects {affected_products} products."
                })
                
        # 3. Compile Simulation Result
        # Calculate a mock confidence score based on data availability
        confidence = 0.85 if len(violations) == 0 else 0.40
        
        result_data = {
            "baseline": baseline_state,
            "simulated": simulated_state,
            "risks_detected": risks_detected,
            "metrics": {
                "total_risks": len(risks_detected)
            }
        }
        
        result = SimulationResult(
            scenario_id=scenario.id,
            result_data=result_data,
            confidence_score=confidence,
            constraint_violations=violations,
            status='COMPLETED'
        )
        
        db.session.add(result)
        db.session.commit()
        
        # 4. Escalate critical risks to the OperationalRisk tracker (Milestone 8)
        for r in risks_detected:
            op_risk = OperationalRisk(
                institution_id=scenario.institution_id,
                risk_type=r['type'],
                title=f"Simulated Risk: {r['message']}",
                probability=0.7, # Mocked simulation probability
                impact_score=8.0 if r['impact'] in ['HIGH', 'CRITICAL'] else 4.0,
                urgency=r['impact'],
                simulation_result_id=result.id,
                context_data=json.dumps({"scenario_id": scenario.id})
            )
            db.session.add(op_risk)
            
        db.session.commit()
        return result
