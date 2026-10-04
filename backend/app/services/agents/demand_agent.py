import json
from app.services.agents.base_agent import BaseAgent, agent_tool
from app.models.predictive import PredictiveForecast
from app.extensions import db
from datetime import datetime, timezone

class DemandAgent(BaseAgent):
    """
    Milestone 8: Demand Agent
    Monitors demand trends and forecasts future loads.
    """
    def __init__(self):
        super().__init__()
        self.agent_id = 'DEMAND_AGENT'
        self.agent_name = 'Demand Intelligence Agent'
        self.purpose = 'Forecast demand and identify anomalies'

    @agent_tool('get_demand_forecast', 'Retrieves the current forecast for an item', is_high_risk=False)
    def get_demand_forecast(self, task, product_id):
        forecast = PredictiveForecast.query.filter_by(
            product_id=product_id
        ).order_by(PredictiveForecast.forecast_date.desc()).first()
        
        if not forecast:
            return {"error": "No forecast available"}
            
        return {
            "forecast_date": forecast.forecast_date.isoformat(),
            "expected_demand": forecast.predicted_quantity,
            "confidence": getattr(forecast, 'confidence_score', getattr(forecast, 'confidence', 'MEDIUM')),
            "is_high_demand": forecast.predicted_quantity > 100 # Mock threshold
        }

    def process_task(self, task):
        payload = task.input_payload
        action = payload.get('action')
        
        if action == 'ANALYZE_DEMAND_SURGE':
            product_id = payload.get('product_id')
            forecast = self.get_demand_forecast(task, product_id)
            
            if forecast.get('is_high_demand'):
                return {
                    "result": "SURGE_DETECTED",
                    "reason": f"Expected demand ({forecast['expected_demand']}) exceeds normal baseline.",
                    "evidence": forecast,
                    "recommend_action": {
                        "agent": "INVENTORY_AGENT",
                        "action": "CHECK_STOCKOUT_RISK",
                        "product_id": product_id
                    }
                }
            return {
                "result": "NORMAL",
                "reason": "Demand is within normal bounds.",
                "evidence": forecast
            }
            
        raise ValueError(f"Unknown DemandAgent action: {action}")
