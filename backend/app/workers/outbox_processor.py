import time
from app import create_app
from app.extensions import db
from app.models.outbox import OutboxEvent
import requests

def process_outbox(app):
    with app.app_context():
        app.logger.info("Outbox processor started.")
        while True:
            try:
                # Find pending events (locking rows to prevent concurrent processing in HA setup)
                # Since we use SQLite, we can't easily do SELECT FOR UPDATE SKIP LOCKED
                # We'll just fetch un-processed
                events = OutboxEvent.query.filter_by(processed=False).order_by(OutboxEvent.created_at.asc()).limit(50).all()
                
                for event in events:
                    try:
                        app.logger.info(f"Processing event {event.id} ({event.event_type})")
                        
                        # In a real setup, we would publish to RabbitMQ/Kafka here.
                        # For now, we will hit an internal webhook or push to a Redis queue.
                        # Since we only have socketio, we might need a way to trigger socketio externally.
                        # Flask-SocketIO supports message queues (like Redis) via external processes.
                        # For our current MVP architecture, we can assume this worker connects to the same redis instance.
                        
                        # Just mark as processed for now to simulate the transactional outbox pattern working
                        event.processed = True
                        event.processed_at = db.func.now()
                        db.session.commit()
                        app.logger.info(f"Successfully processed event {event.id}")
                    except Exception as e:
                        db.session.rollback()
                        app.logger.error(f"Failed to process event {event.id}: {e}")
                        
                        # Implement Retry policy with DLQ
                        if event.retry_count >= 3:
                            event.processed = True # Mark true but we will store error to signify DLQ
                            event.error = 'FAILED_DLQ'
                        else:
                            event.retry_count += 1
                        db.session.commit()
            
                time.sleep(2) # Polling interval
            except Exception as e:
                app.logger.error(f"Outbox processor encountered an error: {e}")
                db.session.rollback()
                time.sleep(5) # Backoff on error

if __name__ == '__main__':
    app = create_app()
    process_outbox(app)
