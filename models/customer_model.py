from datetime import datetime, UTC
from extensions import db


class CustomerStatus:
    """A self-registered customer starts Pending until an Officer verifies
    the meter number against utility records (see registration workflow)."""
    PENDING = "Pending"
    ACTIVE = "Active"


class Customer(db.Model):
    """Registered water consumer. SRS §7.1 / FR-2."""
    __tablename__ = "customers"

    customer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    meter_no = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default=CustomerStatus.PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    user_account = db.relationship("User", back_populates="customer", uselist=False)

    def __repr__(self):
        return f"<Customer {self.customer_id}: {self.name}>"
