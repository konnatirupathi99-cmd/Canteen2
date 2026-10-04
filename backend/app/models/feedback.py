from ..extensions import db
from datetime import datetime

class CustomerFeedback(db.Model):
    __tablename__ = 'customer_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='SET NULL'), nullable=True)
    stall_id = db.Column(db.Integer, db.ForeignKey('stalls.id', ondelete='CASCADE'), nullable=True, index=True)
    institution_id = db.Column(db.Integer, db.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=True, index=True)
    
    rating = db.Column(db.Integer, nullable=False) # 1-5
    comment = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True) # FOOD_QUALITY, WAIT_TIME, SERVICE, PRICE
    
    processed_for_intelligence = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<CustomerFeedback {self.rating}/5 from {self.customer_id}>"
