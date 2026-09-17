from datetime import datetime
from extensions import db

class CustomerStatus:
    PENDING = "Pending"
    ACTIVE = "Active"
    REJECTED = "Rejected"
    DISCONNECTED = "Disconnected"

class Customer(db.Model):
    __tablename__ = "customers"

    customer_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=True)
    meter_no = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default=CustomerStatus.PENDING)
    zone = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    verified_by = db.Column(db.Integer, nullable=True)

    user_account = db.relationship("User", back_populates="customer", uselist=False)

    @staticmethod
    def generate_meter_no():
        year = datetime.now().year
        last = Customer.query.order_by(Customer.customer_id.desc()).first()
        if last and last.meter_no.startswith(str(year)):
            try:
                seq = int(last.meter_no[-4:]) + 1
            except:
                seq = 1
        else:
            seq = 1
        return f"{year}{seq:04d}"

    def __repr__(self):
        return f"<Customer {self.customer_id}: {self.name}>"
