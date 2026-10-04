import logging
from datetime import datetime, timedelta
import json
from app.extensions import db
from app.models import (
    IntelligenceSignal, Recommendation, RecommendationAudit,
    Product, Inventory, OrderItem, Fulfillment
)
from sqlalchemy import func

logger = logging.getLogger(__name__)

class IntelligenceService:
    @staticmethod
    def get_real_time_snapshot(canteen_id=None):
        """
        Milestone 2: Real-Time Operational Snapshot
        Gathers active orders, kitchen load, and critical stock items.
        """
        # Active Orders
        active_statuses = ['CONFIRMED', 'ACCEPTED', 'PREPARING', 'READY']
        active_fulfillments = Fulfillment.query.filter(Fulfillment.status.in_(active_statuses)).all()
        
        active_count = len(active_fulfillments)
        
        # Calculate recent velocity (orders in last 15 mins)
        fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
        recent_fulfillments = Fulfillment.query.filter(Fulfillment.created_at >= fifteen_mins_ago).count()
        orders_per_minute = round(recent_fulfillments / 15.0, 2)
        
        # Critical Stock Items
        critical_inventory = Inventory.query.filter(
            Inventory.quantity <= Inventory.low_stock_threshold,
            Inventory.quantity > 0
        ).count()
        stockouts = Inventory.query.filter(Inventory.quantity == 0).count()
        
        # Mock calculation for kitchen utilization for MVP
        # Say max capacity is 50 orders/hr
        kitchen_util = min(100, int((active_count / 50.0) * 100))
        
        health_score = 100
        health_score -= (stockouts * 5)
        health_score -= (critical_inventory * 2)
        if kitchen_util > 90:
            health_score -= 10
        elif kitchen_util > 80:
            health_score -= 5
            
        health_score = max(0, health_score)
        
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "active_orders": active_count,
            "orders_per_minute": orders_per_minute,
            "kitchen_utilization_percent": kitchen_util,
            "critical_stock_items": critical_inventory,
            "stockouts": stockouts,
            "operational_health_score": health_score
        }
        
        return snapshot

    @staticmethod
    def generate_stockout_risk_signal(product_id, stall_id=None):
        """
        Milestone 4: Stockout Risk Engine
        Evaluates current inventory and consumption rate to predict stockouts.
        """
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if not inventory or inventory.quantity <= 0:
            return None
            
        # Get sales in last 1 hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_sales = db.session.query(func.sum(OrderItem.quantity)).join(Fulfillment).filter(
            OrderItem.product_id == product_id,
            Fulfillment.created_at >= one_hour_ago
        ).scalar() or 0
        
        if recent_sales == 0:
            return None # Not enough data
            
        # Extrapolate
        estimated_hours_left = inventory.quantity / float(recent_sales)
        
        severity = 'LOW'
        if estimated_hours_left < 1:
            severity = 'CRITICAL'
        elif estimated_hours_left < 3:
            severity = 'HIGH'
        elif estimated_hours_left < 6:
            severity = 'MEDIUM'
            
        if severity in ['HIGH', 'CRITICAL']:
            signal = IntelligenceSignal(
                type='INVENTORY_ANOMALY',
                severity=severity,
                message=f"Imminent stockout risk. Estimated {round(estimated_hours_left, 1)} hours left.",
                context_data=json.dumps({
                    "product_id": product_id,
                    "quantity_remaining": inventory.quantity,
                    "consumption_per_hour": recent_sales
                }),
                stall_id=stall_id
            )
            db.session.add(signal)
            db.session.commit()
            return signal
        return None

    @staticmethod
    def create_recommendation(type, reason, suggested_action, priority='MEDIUM', confidence=0.0, product_id=None, stall_id=None):
        # Deduplication (Milestone 11)
        # Check if an identical OPEN recommendation already exists
        existing = Recommendation.query.filter_by(
            type=type,
            product_id=product_id,
            stall_id=stall_id,
            status='GENERATED'
        ).first()
        
        if existing:
            # Update confidence/priority if needed, but do not create a duplicate
            if confidence > existing.confidence:
                existing.confidence = confidence
            if priority in ['HIGH', 'CRITICAL'] and existing.priority not in ['HIGH', 'CRITICAL']:
                existing.priority = priority
            db.session.commit()
            return existing

        rec = Recommendation(
            type=type,
            reason=reason,
            suggested_action=json.dumps(suggested_action),
            priority=priority,
            confidence=confidence,
            product_id=product_id,
            stall_id=stall_id
        )
        db.session.add(rec)
        db.session.commit()
        return rec

    @staticmethod
    def generate_demand_surge_signal(product_id, stall_id=None):
        """
        Milestone 5: Demand Intelligence
        Detects if current demand is abnormally high compared to expected.
        """
        # Look at last 15 mins sales
        fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
        recent_sales = db.session.query(func.sum(OrderItem.quantity)).join(Fulfillment).filter(
            OrderItem.product_id == product_id,
            Fulfillment.created_at >= fifteen_mins_ago
        ).scalar() or 0
        
        # Historical baseline: say we expect 2 per 15 min. (Ideally comes from Predictive service)
        baseline = 2
        
        if recent_sales > (baseline * 3): # 300% surge
            signal = IntelligenceSignal(
                type='DEMAND_SURGE',
                severity='HIGH',
                message=f"Demand surge detected! Sold {recent_sales} in last 15m (baseline {baseline}).",
                context_data=json.dumps({
                    "product_id": product_id,
                    "recent_sales": recent_sales,
                    "baseline": baseline
                }),
                stall_id=stall_id
            )
            db.session.add(signal)
            
            # Auto-generate a recommendation to increase preparation or reorder
            rec = IntelligenceService.create_recommendation(
                type='INCREASE_PREPARATION',
                reason=f"Demand surged by {round((recent_sales/baseline)*100)}%. Increase preparation to prevent queue buildup.",
                suggested_action={"action": "increase_prep", "product_id": product_id, "amount": int(recent_sales * 1.5)},
                priority='HIGH',
                confidence=0.85,
                product_id=product_id,
                stall_id=stall_id
            )
            return signal, rec
            
        return None, None

    @staticmethod
    def generate_kitchen_bottleneck_signal(stall_id):
        """
        Milestone 6: Kitchen Capacity Intelligence
        Detects if a specific stall/kitchen is overwhelmed.
        """
        active_statuses = ['ACCEPTED', 'PREPARING']
        active_fulfillments = Fulfillment.query.filter(
            Fulfillment.stall_id == stall_id,
            Fulfillment.status.in_(active_statuses)
        ).all()
        
        # Suppose a stall can comfortably handle 10 orders at a time
        max_comfortable_capacity = 10
        current_load = len(active_fulfillments)
        
        if current_load > max_comfortable_capacity:
            severity = 'HIGH' if current_load > (max_comfortable_capacity * 1.5) else 'MEDIUM'
            
            signal = IntelligenceSignal(
                type='KITCHEN_ANOMALY',
                severity=severity,
                message=f"Kitchen bottleneck detected! {current_load} active orders (capacity {max_comfortable_capacity}).",
                context_data=json.dumps({
                    "stall_id": stall_id,
                    "current_load": current_load,
                    "capacity": max_comfortable_capacity
                }),
                stall_id=stall_id
            )
            db.session.add(signal)
            
            rec = IntelligenceService.create_recommendation(
                type='ADJUST_STAFF',
                reason=f"Kitchen load is {int((current_load/max_comfortable_capacity)*100)}% of comfortable capacity. Consider reassigning staff.",
                suggested_action={"action": "add_staff", "stall_id": stall_id, "amount": 1},
                priority=severity,
                confidence=0.88,
                product_id=None,
                stall_id=stall_id
            )
            
            db.session.commit()
            return signal, rec
            
        return None, None

    @staticmethod
    def predict_eta(order_id):
        """
        Milestone 46: ETA Prediction
        Estimates order completion time using current queue and historical data.
        """
        from app.models import Order
        order = Order.query.get(order_id)
        if not order or order.status not in ['PLACED', 'PAYMENT_PENDING', 'CONFIRMED', 'ACCEPTED', 'PREPARING']:
            return {"eta_minutes": 0, "confidence": 1.0}
            
        max_eta = 0
        for fulfillment in order.fulfillments:
            # Get active orders in front of this one at the same stall
            active_ahead = Fulfillment.query.filter(
                Fulfillment.stall_id == fulfillment.stall_id,
                Fulfillment.status.in_(['ACCEPTED', 'PREPARING']),
                Fulfillment.id < fulfillment.id
            ).count()
            
            # Assume 2 mins per order ahead + 5 mins base prep time
            stall_eta = 5 + (active_ahead * 2)
            if stall_eta > max_eta:
                max_eta = stall_eta
                
        # Return ETA and Confidence (lower confidence if ETA is high)
        confidence = max(0.4, 1.0 - (max_eta * 0.01))
        
        return {
            "eta_minutes": max_eta,
            "confidence": round(confidence, 2)
        }

    @staticmethod
    def generate_supplier_risk_signal(product_id):
        """
        Milestone 7: Supplier Risk Intelligence
        Detects if suppliers are reliable for a critical product.
        """
        from app.models import SupplierProduct
        suppliers = SupplierProduct.query.filter_by(product_id=product_id).all()
        
        if not suppliers:
            return None, None
            
        # Example logic: if all suppliers for this product have low reliability (< 80%) or long lead times (> 48h)
        risk_score = 0
        for sp in suppliers:
            if sp.reliability_score < 0.80:
                risk_score += 1
            if sp.lead_time_hours > 48:
                risk_score += 1
                
        if risk_score >= len(suppliers):
            signal = IntelligenceSignal(
                type='SUPPLIER_ANOMALY',
                severity='HIGH',
                message=f"High supplier risk for product. Active suppliers are unreliable or have long lead times.",
                context_data=json.dumps({
                    "product_id": product_id,
                    "supplier_count": len(suppliers)
                })
            )
            db.session.add(signal)
            
            rec = IntelligenceService.create_recommendation(
                type='FIND_ALTERNATIVE_SUPPLIER',
                reason="Current supply chain for this product is vulnerable to delays.",
                suggested_action={"action": "flag_procurement_review", "product_id": product_id},
                priority='HIGH',
                confidence=0.95,
                product_id=product_id
            )
            
            db.session.commit()
            return signal, rec
            
        return None, None

    @staticmethod
    def generate_waste_risk_signal(product_id, stall_id=None):
        """
        Milestone 10: Waste Intelligence and Prediction
        Detects if an item is likely to become waste (high stock, low demand).
        """
        from app.services.forecast_service import ForecastService
        from datetime import date
        
        inventory = Inventory.query.filter_by(product_id=product_id).first()
        if not inventory or inventory.quantity <= 0:
            return None, None
            
        # Get today's forecast
        forecast = ForecastService.get_effective_forecast(product_id, date.today(), 'DAY')
        if not forecast:
            return None, None
            
        expected_demand = forecast['quantity']
        
        # If we have more than double the expected demand in stock for a perishable
        # (Assuming all Canteen food items are somewhat perishable for the day)
        if inventory.quantity > (expected_demand * 1.5):
            waste_risk_qty = int(inventory.quantity - expected_demand)
            
            signal = IntelligenceSignal(
                type='WASTE_RISK',
                severity='MEDIUM',
                message=f"High waste probability. {waste_risk_qty} units above expected demand.",
                context_data=json.dumps({
                    "product_id": product_id,
                    "current_stock": inventory.quantity,
                    "expected_demand": expected_demand,
                    "waste_risk_qty": waste_risk_qty
                }),
                stall_id=stall_id
            )
            db.session.add(signal)
            
            rec = IntelligenceService.create_recommendation(
                type='WASTE_MITIGATION',
                reason=f"Current stock ({inventory.quantity}) exceeds expected demand ({expected_demand}).",
                suggested_action={"action": "run_promotion", "product_id": product_id, "discount_pct": 20},
                priority='MEDIUM',
                confidence=forecast.get('confidence', 0.8),
                product_id=product_id,
                stall_id=stall_id
            )
            
            db.session.commit()
            return signal, rec
            
        return None, None

    @staticmethod
    def generate_procurement_optimization(institution_id):
        """
        Milestone 9: Procurement Optimization
        Recommends purchases based on Demand, Lead Time, MOQ, Budget, and Storage.
        Also consolidates purchases (Point 35).
        """
        from app.models import GlobalProduct, Inventory, SupplierProduct
        
        # 1. Identify all products across all canteens in the institution that need restocking
        low_stock_items = Inventory.query.join(Product).join(GlobalProduct).filter(
            GlobalProduct.institution_id == institution_id,
            Inventory.quantity <= Inventory.low_stock_threshold
        ).all()
        
        if not low_stock_items:
            return []
            
        recommendations = []
        # Group by global_product_id to consolidate
        grouped_needs = {}
        for inv in low_stock_items:
            gp_id = inv.product.global_product_id
            if gp_id not in grouped_needs:
                grouped_needs[gp_id] = 0
            # Need = reorder_level - current (simple)
            grouped_needs[gp_id] += max(0, inv.low_stock_threshold - inv.quantity + 50) # +50 safety stock for now
            
        for gp_id, total_needed in grouped_needs.items():
            # Find best supplier based on price and reliability
            suppliers = SupplierProduct.query.filter_by(product_id=gp_id).all()
            if not suppliers:
                continue
                
            # Multi-objective ranking: Price (lower is better), Reliability (higher is better), Lead time (lower is better)
            best_supplier = min(suppliers, key=lambda s: (s.unit_price * 10) - (s.reliability_score * 100) + (s.lead_time_hours * 2))
            
            # MOQ logic
            order_qty = max(total_needed, best_supplier.minimum_order_quantity)
            total_cost = order_qty * best_supplier.unit_price
            
            # Budget Check
            from app.services.policy_service import PolicyService
            monthly_budget = PolicyService.evaluate('MONTHLY_PROCUREMENT_BUDGET', 50000, institution_id=institution_id)
            # In a real system, we'd sum up current month's expenses. Let's mock a budget risk if single order > 20% of budget
            budget_risk = ""
            if float(total_cost) > (float(monthly_budget) * 0.2):
                budget_risk = " (WARNING: Consumes >20% of monthly budget)"
            
            rec = IntelligenceService.create_recommendation(
                type='CONSOLIDATED_PROCUREMENT',
                reason=f"Consolidated need of {total_needed} units. Best supplier: {best_supplier.supplier_id}.{budget_risk}",
                suggested_action={"action": "create_purchase_order", "global_product_id": gp_id, "supplier_id": best_supplier.supplier_id, "quantity": order_qty},
                priority='HIGH' if total_needed > 100 else 'MEDIUM',
                confidence=0.90
            )
            recommendations.append(rec)
            
        db.session.commit()
        return recommendations

    @staticmethod
    def simulate_scenario(scenario_type, params, institution_id=None):
        """
        Milestone 10: What-If Simulation
        Evaluates hypothetical scenarios using the Digital Twin engine.
        """
        from app.services.twin_service import DigitalTwinService
        from app.models.twin import SimulationScenario
        from app.services.simulation_engine import SimulationEngine
        
        # 1. Generate an isolated snapshot
        snapshot = DigitalTwinService.generate_snapshot(institution_id, name="Ad-hoc Intelligence Simulation")
        
        # 2. Create scenario
        scenario = SimulationScenario(
            institution_id=institution_id,
            name=f"Auto-Simulation: {scenario_type}",
            scenario_type=scenario_type,
            base_snapshot_id=snapshot.id,
            parameters=params
        )
        db.session.add(scenario)
        db.session.commit()
        
        # 3. Run simulation
        result = SimulationEngine.run_scenario(scenario)
        
        return result.result_data
