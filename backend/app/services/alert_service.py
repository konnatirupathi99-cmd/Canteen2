from app.extensions import db, socketio
from app.models.alert import Alert
from datetime import datetime
import uuid

class AlertService:
    
    @staticmethod
    def trigger_alert(alert_type, severity, message, product_id=None, stall_id=None, deduplication_key=None):
        """
        Triggers an alert. If an ACTIVE alert with the same deduplication_key exists,
        it just updates last_triggered_at (deduplication).
        """
        if deduplication_key:
            existing = Alert.query.filter_by(
                deduplication_key=deduplication_key,
                status='ACTIVE'
            ).first()
            
            if existing:
                existing.last_triggered_at = datetime.utcnow()
                db.session.commit()
                return existing, False # False means not newly created
                
        # Create new alert
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            product_id=product_id,
            stall_id=stall_id,
            deduplication_key=deduplication_key
        )
        db.session.add(alert)
        db.session.commit()
        
        # Broadcast the new alert to managers
        socketio.emit('NEW_ALERT', {
            "id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "timestamp": alert.created_at.isoformat()
        }, room='managers')
        
        return alert, True

    @staticmethod
    def resolve_alert_by_key(deduplication_key):
        """
        Resolves an active alert automatically when the condition clears.
        """
        alerts = Alert.query.filter_by(
            deduplication_key=deduplication_key,
            status='ACTIVE'
        ).all()
        
        for alert in alerts:
            alert.status = 'RESOLVED'
            alert.resolved_at = datetime.utcnow()
            
            socketio.emit('ALERT_RESOLVED', {
                "id": alert.id,
                "deduplication_key": deduplication_key
            }, room='managers')
            
        db.session.commit()
