import hmac
import hashlib
import json
import requests
from datetime import datetime
from app.models.webhook import WebhookSubscription, WebhookDelivery
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

class WebhookService:
    @staticmethod
    def sign_payload(secret, payload):
        """Generates HMAC-SHA256 signature for the payload"""
        if not isinstance(payload, str):
            payload = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    @staticmethod
    def dispatch_event(event):
        """
        Dispatches an OutboxEvent to all relevant active webhook subscriptions.
        Returns the number of deliveries queued/sent.
        """
        # Find subscriptions that are ACTIVE, belong to the event's institution (or are global), 
        # and subscribe to this event_type
        
        subscriptions = WebhookSubscription.query.filter_by(status='ACTIVE').all()
        
        deliveries = []
        for sub in subscriptions:
            # Check institution match if event has one
            if sub.institution_id and event.institution_id and sub.institution_id != event.institution_id:
                continue
                
            # Check event type
            if event.event_type not in sub.event_types:
                continue
                
            delivery = WebhookDelivery(
                subscription_id=sub.id,
                event_id=event.id,
                status='PENDING'
            )
            db.session.add(delivery)
            deliveries.append((sub, delivery))
            
        db.session.commit()
        
        # Fire deliveries immediately for this MVP. In production, this goes to a Celery queue.
        for sub, delivery in deliveries:
            WebhookService._send_delivery(sub, delivery, event)
            
        return len(deliveries)
        
    @staticmethod
    def _send_delivery(subscription, delivery, event):
        payload_dict = {
            "event_id": event.id,
            "event_type": event.event_type,
            "version": event.version,
            "timestamp": event.created_at.isoformat(),
            "producer": event.producer,
            "correlation_id": event.correlation_id,
            "payload": event.payload
        }
        
        payload_str = json.dumps(payload_dict)
        signature = WebhookService.sign_payload(subscription.secret, payload_str)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': f'sha256={signature}',
            'X-Webhook-Event': event.event_type,
            'X-Webhook-Event-Id': event.id
        }
        
        try:
            # Short timeout to avoid blocking core threads
            response = requests.post(subscription.url, data=payload_str, headers=headers, timeout=3)
            
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000] # truncate
            
            if 200 <= response.status_code < 300:
                delivery.status = 'SUCCESS'
            else:
                delivery.status = 'FAILED'
                
        except Exception as e:
            logger.error(f"Webhook delivery failed: {str(e)}")
            delivery.status = 'FAILED'
            delivery.response_body = str(e)[:1000]
            
        delivery.completed_at = datetime.utcnow()
        db.session.commit()
