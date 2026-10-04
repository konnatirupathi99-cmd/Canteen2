import time
from app import create_app
from app.extensions import db
from app.models.product import Product
from app.services.forecast_service import ForecastService
from app.services.intelligence_service import IntelligenceService
from datetime import datetime

def run_intelligence_processor(app):
    """
    Background worker that handles AI analytics and intelligence loops.
    Runs asynchronously to isolate AI loads from transactional POS loads.
    """
    with app.app_context():
        app.logger.info("Intelligence processor started.")
        while True:
            try:
                # 1. Generate Baseline Forecasts for all active products
                # Run this only once a day in reality, but for demo we can run it on loop
                # Just checking if today's forecast exists
                app.logger.info("Running Baseline Forecasting...")
                products = Product.query.filter_by(is_active=True).all()
                for product in products:
                    try:
                        ForecastService.generate_baseline_forecast(product.id)
                    except Exception as e:
                        app.logger.error(f"Error forecasting product {product.id}: {e}")

                # 2. Check for Waste Risk (Milestone 10)
                app.logger.info("Checking Waste Risks...")
                for product in products:
                    try:
                        IntelligenceService.generate_waste_risk_signal(product.id, stall_id=product.stall_id)
                    except Exception as e:
                        app.logger.error(f"Error checking waste for {product.id}: {e}")

                # 3. Check for Stockout Risks (Milestone 8)
                app.logger.info("Checking Stockout Risks...")
                for product in products:
                    try:
                        IntelligenceService.generate_stockout_risk_signal(product.id, stall_id=product.stall_id)
                    except Exception as e:
                        app.logger.error(f"Error checking stockout for {product.id}: {e}")

                # 4. Check for Kitchen Bottlenecks (Milestone 12)
                app.logger.info("Checking Kitchen Bottlenecks...")
                from app.models.stall import Stall
                stalls = Stall.query.filter_by(is_active=True).all()
                for stall in stalls:
                    try:
                        IntelligenceService.generate_kitchen_bottleneck_signal(stall.id)
                    except Exception as e:
                        app.logger.error(f"Error checking bottleneck for stall {stall.id}: {e}")
                
                # 5. Clean up expired recommendations
                app.logger.info("Cleaning up expired recommendations...")
                from app.models.intelligence import Recommendation
                expired = Recommendation.query.filter(
                    Recommendation.status.in_(['GENERATED', 'REVIEWED']),
                    Recommendation.expires_at < datetime.utcnow()
                ).all()
                for req in expired:
                    req.status = 'EXPIRED'
                db.session.commit()
                
                # 6. Phase 24: Run Optimization Engine & Policy Automation (Milestone 16, 57)
                app.logger.info("Running Optimization Engine...")
                try:
                    from app.services.optimization_engine import OptimizationEngine
                    from app.models.organization import Institution
                    
                    institutions = Institution.query.all()
                    for inst in institutions:
                        # 6a. Generate Resource Optimizations
                        recs = OptimizationEngine.run_optimization(inst.id, objective_profile='BALANCED')
                        
                        # 6b. Evaluate and Execute via Policy Engine
                        if recs:
                            OptimizationEngine.trigger_automated_policies(inst.id, recs)
                            app.logger.info(f"Triggered policies for {len(recs)} optimization recommendations on Tenant {inst.id}.")
                            
                except Exception as e:
                    app.logger.error(f"Error in Optimization Engine loop: {e}")
                
                # 7. Phase 25: Self-Monitoring, Anomaly Detection & Orchestration
                app.logger.info("Running Anomaly Engine and Orchestrator...")
                try:
                    from app.services.anomaly_engine import AnomalyEngine
                    from app.services.twin_sync import DigitalTwinSyncService
                    from app.services.orchestrator import OperationalOrchestrator
                    from app.models.orchestration import Workflow
                    from app.models.organization import Institution
                    
                    institutions = Institution.query.all()
                    for inst in institutions:
                        # 7a. Digital Twin Synchronization & Divergence Check (MILESTONE 7, 8)
                        DigitalTwinSyncService.check_health_and_divergence(inst.id)
                        
                        # 7b. Anomaly Detection -> Creates Incidents -> Triggers Mitigation Workflows (MILESTONE 13, 14, 44)
                        AnomalyEngine.detect_anomalies(inst.id)
                        
                        # 7c. Execute pending workflows (MILESTONE 5)
                        pending_workflows = Workflow.query.filter(
                            Workflow.tenant_id == inst.id,
                            Workflow.status.in_(['CREATED', 'WAITING'])
                        ).all()
                        for wf in pending_workflows:
                            app.logger.info(f"Executing workflow {wf.name} ({wf.id})")
                            OperationalOrchestrator.execute_workflow(wf.id)
                            
                except Exception as e:
                    app.logger.error(f"Error in Phase 25 Orchestration loop: {e}")
                
                # Polling interval (1 hour for a real app, 15s for demo)
                time.sleep(15) 
            except Exception as e:
                app.logger.error(f"Intelligence processor encountered an error: {e}")
                db.session.rollback()
                time.sleep(10)

if __name__ == '__main__':
    app = create_app()
    run_intelligence_processor(app)
