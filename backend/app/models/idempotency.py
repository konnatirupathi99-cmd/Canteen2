from ..extensions import db
from datetime import datetime, timezone

class IdempotencyRecord(db.Model):
    __tablename__ = 'idempotency_records'

    idempotency_key = db.Column(db.String(255), primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # or user_id
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    request_hash = db.Column(db.String(255), nullable=False)
    response_body = db.Column(db.Text, nullable=True)
    response_status_code = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<IdempotencyRecord {self.idempotency_key}>"
