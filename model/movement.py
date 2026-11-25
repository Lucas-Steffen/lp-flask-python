from datetime import datetime, timezone

from app import db


class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    type = db.Column(db.String(3), nullable=False)  # "IN" (entrada) ou "OUT" (saída)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "user_id": self.user_id,
            "type": self.type,
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return '<Movement %r %r>' % (self.type, self.quantity)
