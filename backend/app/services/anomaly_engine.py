import logging
from datetime import datetime, timezone
import json
from app.extensions import db
from app.models.orchestration import OperationalIncident
from app.services.orchestrator import OperationalOrchestrator

logger = logging.getLogger(__name__)

class AnomalyEngine:
    """
    Phase 25: Anomaly Engine
    Continuously monitors system state, detects anomalies, correlates them into Incidents,
    and optionally triggers automated mitigation workflows.
    """

    @staticmethod
    def detect_anomalies(tenant_id):
        """
        MILESTONE 13: Detect Anomalies
        Evaluates operational state and detects deviations from expectations.
        """
        from app.services.twin_service import DigitalTwinService
        snapshot = DigitalTwinService.generate_snapshot(tenant_id, name="Anomaly Detection Scan")
        state = snapshot.state_data
        
        detected = []
        
        # 1. Inventory Anomalies (e.g. Stock dropping much faster than forecast)
        for product_id, inv_data in state.get('inventory', {}).items():
            qty = inv_data['quantity']
            low_stock = inv_data['low_stock_threshold']
            
            # Very basic anomaly check for MVP
            if qty < (low_stock * 0.5):
                detected.append({
                    "type": "InventoryAnomaly",
                    "severity": "HIGH",
                    "title": f"Critical Stock Depletion for Product {product_id}",
                    "affected_service": "Inventory",
                    "context": {"product_id": product_id, "qty": qty, "threshold": low_stock}
                })

        # 2. Kitchen / Queue Anomalies
        for stall_id, load in state.get('active_orders', {}).items():
            capacity = state.get('stalls', {}).get(stall_id, {}).get('capacity', 10)
            if load > (capacity * 1.5): # 150% load
                detected.append({
                    "type": "QueueAnomaly",
                    "severity": "CRITICAL",
                    "title": f"Severe Kitchen Bottleneck at Stall {stall_id}",
                    "affected_service": "KDS",
                    "context": {"stall_id": stall_id, "load": load, "capacity": capacity}
                })
                
        # Handle detected anomalies
        for anomaly in detected:
            AnomalyEngine._process_anomaly(tenant_id, anomaly)

    @staticmethod
    def _process_anomaly(tenant_id, anomaly):
        """
        MILESTONE 14: Incident Management & Correlation
        """
        # Simple correlation: Check if an OPEN incident already exists for this service & type
        existing = OperationalIncident.query.filter_by(
            tenant_id=tenant_id,
            anomaly_type=anomaly['type'],
            affected_service=anomaly['affected_service'],
            status='OPEN'
        ).first()
        
        if existing:
            # Correlate / Update
            context = json.loads(existing.context_data) if existing.context_data else {}
            context['latest_event'] = anomaly['context']
            existing.context_data = json.dumps(context)
            db.session.commit()
            logger.info(f"Correlated anomaly into existing incident {existing.id}")
            return existing
            
        # Create new incident
        incident = OperationalIncident(
            tenant_id=tenant_id,
            title=anomaly['title'],
            severity=anomaly['severity'],
            anomaly_type=anomaly['type'],
            affected_service=anomaly['affected_service'],
            context_data=json.dumps(anomaly['context'])
        )
        db.session.add(incident)
        db.session.commit()
        
        # Trigger automated mitigation if applicable (MILESTONE 44)
        if incident.severity in ['INFO', 'LOW', 'MEDIUM']:
            # Auto-mitigate via workflow
            workflow = OperationalOrchestrator.start_workflow(
                tenant_id=tenant_id,
                name="IncidentMitigation",
                correlation_id=f"inc_{incident.id}",
                idempotency_key=f"mitigate_{incident.id}_{incident.detected_at.timestamp()}",
                context_data={"incident_id": incident.id}
            )
            incident.workflow_id = workflow.id
            incident.status = 'MITIGATING'
            db.session.commit()
            
            # The worker/orchestrator will pick this up and execute it
            OperationalOrchestrator.execute_workflow(workflow.id)
            
        return incident
