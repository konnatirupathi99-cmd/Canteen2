from app.extensions import db
from app.models.predictive import Forecast, DemandAnomaly, DemandEvent, ForecastOverride
from app.models.order import OrderItem, Order
from app.models.inventory import Inventory
from app.models.product import Product
from app.services.alert_service import AlertService
from datetime import datetime, timedelta, date
from sqlalchemy import func

class ForecastingService:
    @staticmethod
    def get_historical_demand(product_id, days=7):
        """
        Aggregate gross fulfilled demand for the last N days.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        results = db.session.query(
            func.date(Order.created_at).label('order_date'),
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(Order, Order.id == OrderItem.order_id)\
         .filter(OrderItem.product_id == product_id)\
         .filter(Order.status == 'FULFILLED')\
         .filter(Order.created_at >= start_date)\
         .filter(Order.created_at <= end_date)\
         .group_by(func.date(Order.created_at)).all()
         
        demand_map = {str(r.order_date): float(r.total_quantity) for r in results}
        
        # Fill missing days with 0 (assuming menu availability - which we should ideally check, but for MVP this is OK)
        history = []
        for i in range(days):
            dt_str = str((start_date + timedelta(days=i)).date())
            history.append(demand_map.get(dt_str, 0))
            
        return history

    @staticmethod
    def generate_baseline_forecast(product_id, target_date):
        """
        Generates a baseline forecast based on moving average and day-of-week logic.
        """
        history_30 = ForecastingService.get_historical_demand(product_id, days=30)
        history_7 = history_30[-7:] if len(history_30) >= 7 else history_30
        
        if not history_7 or sum(history_7) == 0:
            return 0, 'LOW'
            
        recent_avg = sum(history_7) / len(history_7)
        
        # Determine confidence
        confidence = 'MEDIUM'
        if len([x for x in history_30 if x > 0]) > 14:
            confidence = 'HIGH'
        if len([x for x in history_7 if x > 0]) < 2:
            confidence = 'LOW'
            
        # Optional: check if there's a DemandEvent
        events = DemandEvent.query.filter_by(event_date=target_date).all()
        multiplier = 1.0
        for e in events:
            multiplier *= float(e.demand_multiplier)
            
        predicted = int(recent_avg * multiplier)
        
        # Anomaly detection (Spike/Drop compared to 30-day baseline)
        if sum(history_30) > 0 and recent_avg > 0:
            baseline_30 = sum(history_30) / len(history_30)
            if baseline_30 > 0:
                deviation = ((recent_avg - baseline_30) / baseline_30) * 100
                if deviation > 30: # 30% spike
                    anomaly = DemandAnomaly(
                        product_id=product_id,
                        baseline=baseline_30,
                        observed=recent_avg,
                        deviation_percentage=deviation,
                        anomaly_type='DEMAND_SPIKE'
                    )
                    db.session.add(anomaly)
                    AlertService.trigger_alert(
                        alert_type='DEMAND_SPIKE',
                        severity='HIGH',
                        message=f"Product {product_id} demand spiked by {deviation:.1f}%",
                        product_id=product_id,
                        deduplication_key=f"spike_{product_id}"
                    )
                elif deviation < -30:
                    anomaly = DemandAnomaly(
                        product_id=product_id,
                        baseline=baseline_30,
                        observed=recent_avg,
                        deviation_percentage=deviation,
                        anomaly_type='DEMAND_DROP'
                    )
                    db.session.add(anomaly)
                    
        return predicted, confidence

    @staticmethod
    def generate_and_save_forecast(product_id, target_date=None):
        if target_date is None:
            target_date = (datetime.utcnow() + timedelta(days=1)).date()
            
        predicted, confidence = ForecastingService.generate_baseline_forecast(product_id, target_date)
        
        # Archive old active forecast for this date
        old = Forecast.query.filter_by(product_id=product_id, forecast_date=target_date, status='ACTIVE').first()
        if old:
            old.status = 'SUPERSEDED'
            
        forecast = Forecast(
            product_id=product_id,
            forecast_date=target_date,
            predicted_quantity=predicted,
            confidence=confidence,
            model_type='MOVING_AVERAGE'
        )
        db.session.add(forecast)
        db.session.commit()
        return forecast

    @staticmethod
    def get_operational_forecast(product_id, target_date):
        forecast = Forecast.query.filter_by(product_id=product_id, forecast_date=target_date, status='ACTIVE').first()
        if not forecast:
            return 0
            
        override = forecast.overrides.order_by(ForecastOverride.created_at.desc()).first()
        if override:
            return override.new_quantity
            
        return forecast.predicted_quantity

    @staticmethod
    def predict_stockout(product_id):
        """
        Projects inventory and predicts if stockout will occur within 3 days.
        Returns: risk_level, projected_stock, expected_eta
        """
        inv = Inventory.query.filter_by(product_id=product_id).first()
        if not inv:
            return 'UNKNOWN', 0, None
            
        current_stock = inv.quantity
        
        # Incoming stock (from POs)
        from app.models.procurement import PurchaseOrderItem, PurchaseOrder
        incoming = db.session.query(func.sum(PurchaseOrderItem.remaining_quantity))\
            .join(PurchaseOrder)\
            .filter(PurchaseOrderItem.product_id == product_id)\
            .filter(PurchaseOrder.status.in_(['SENT', 'CONFIRMED', 'PARTIALLY_RECEIVED']))\
            .scalar() or 0
            
        # Expected demand over next 3 days
        today = datetime.utcnow().date()
        demand_1 = ForecastingService.get_operational_forecast(product_id, today) or 0
        demand_2 = ForecastingService.get_operational_forecast(product_id, today + timedelta(days=1)) or 0
        demand_3 = ForecastingService.get_operational_forecast(product_id, today + timedelta(days=2)) or 0
        
        # We simplify for MVP by just subtracting aggregate
        total_demand = demand_1 + demand_2 + demand_3
        projected = current_stock + incoming - total_demand
        
        risk_level = 'LOW'
        eta = None
        
        if current_stock <= inv.low_stock_threshold:
            risk_level = 'HIGH'
            eta = today
        elif projected < 0:
            risk_level = 'MEDIUM'
            # Estimate when
            if current_stock + incoming - demand_1 < 0:
                eta = today
            elif current_stock + incoming - demand_1 - demand_2 < 0:
                eta = today + timedelta(days=1)
            else:
                eta = today + timedelta(days=2)
                
        return risk_level, projected, eta
