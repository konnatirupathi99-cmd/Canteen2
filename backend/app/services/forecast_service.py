from datetime import datetime, timedelta, date
from app.extensions import db
from app.models.predictive import Forecast, ForecastOverride
from app.models.product import Product
from app.models.order import OrderItem, Fulfillment
from sqlalchemy import func

class ForecastService:
    @staticmethod
    def generate_baseline_forecast(product_id, forecast_date=None, period='DAY'):
        """
        Milestone 6: Baseline Forecasting
        Uses a simple moving average of the last 7 days of similar period.
        """
        if not forecast_date:
            forecast_date = date.today() + timedelta(days=1)
            
        # Get historical sales for this product
        # For simplicity, we just look at the last 7 days from the DB
        start_date = forecast_date - timedelta(days=7)
        
        # Get total quantity sold for this product in the last 7 days
        # We join with Fulfillment to get the created_at timestamp
        sales = db.session.query(
            func.date(Fulfillment.created_at).label('sale_date'),
            func.sum(OrderItem.quantity).label('total_qty')
        ).join(OrderItem, OrderItem.fulfillment_id == Fulfillment.id) \
         .filter(OrderItem.product_id == product_id) \
         .filter(Fulfillment.created_at >= start_date) \
         .filter(Fulfillment.status.in_(['CONFIRMED', 'COMPLETED'])) \
         .group_by('sale_date').all()
         
        total_sales = sum(sale.total_qty for sale in sales) if sales else 0
        days_with_data = len(sales) if sales else 1 # Avoid div by zero
        
        moving_average = int(total_sales / days_with_data) if days_with_data > 0 else 0
        
        # If no sales history, fallback to a cold start logic
        if moving_average == 0:
            moving_average = 10 # Default cold start baseline
            confidence = 'LOW'
        elif days_with_data < 3:
            confidence = 'LOW'
        elif days_with_data < 5:
            confidence = 'MEDIUM'
        else:
            confidence = 'HIGH'

        # Check for existing active forecast
        existing = Forecast.query.filter_by(
            product_id=product_id,
            forecast_date=forecast_date,
            forecast_period=period,
            status='ACTIVE'
        ).first()
        
        if existing:
            # Supersede existing
            existing.status = 'SUPERSEDED'
            db.session.add(existing)
            
        forecast = Forecast(
            product_id=product_id,
            forecast_date=forecast_date,
            forecast_period=period,
            predicted_quantity=moving_average,
            confidence=confidence,
            model_type='MOVING_AVERAGE',
            model_version='v1.0.0',
            status='ACTIVE'
        )
        db.session.add(forecast)
        db.session.commit()
        
        return forecast

    @staticmethod
    def apply_override(forecast_id, user_id, new_quantity, reason):
        """
        Milestone 17: Human approval/override for forecasts
        """
        forecast = Forecast.query.get(forecast_id)
        if not forecast:
            raise ValueError("Forecast not found")
            
        override = ForecastOverride(
            forecast_id=forecast.id,
            overridden_by=user_id,
            new_quantity=new_quantity,
            reason=reason
        )
        db.session.add(override)
        
        # We don't overwrite the predicted_quantity, we keep it for Model Evaluation
        db.session.commit()
        return override

    @staticmethod
    def get_effective_forecast(product_id, forecast_date, period='DAY'):
        """
        Gets the forecast to use (override if exists, else predicted).
        """
        forecast = Forecast.query.filter_by(
            product_id=product_id,
            forecast_date=forecast_date,
            forecast_period=period,
            status='ACTIVE'
        ).first()
        
        if not forecast:
            return None
            
        latest_override = forecast.overrides.order_by(ForecastOverride.created_at.desc()).first()
        if latest_override:
            return {
                "forecast_id": forecast.id,
                "quantity": latest_override.new_quantity,
                "is_overridden": True,
                "confidence": forecast.confidence
            }
            
        return {
            "forecast_id": forecast.id,
            "quantity": forecast.predicted_quantity,
            "is_overridden": False,
            "confidence": forecast.confidence
        }
