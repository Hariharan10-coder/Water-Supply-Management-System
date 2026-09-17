from datetime import datetime
from extensions import db

class MaintenanceStatus:
    PENDING = "Pending"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class MaintenancePriority:
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"

class MaintenanceRequest(db.Model):
    __tablename__ = "maintenance_requests"

    request_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.customer_id"), nullable=False)
    issue_type = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default=MaintenancePriority.MEDIUM)
    status = db.Column(db.String(20), default=MaintenanceStatus.PENDING)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    customer = db.relationship("Customer", backref=db.backref("maintenance_requests", lazy=True))
    assignee = db.relationship("User", foreign_keys=[assigned_to], backref=db.backref("maintenance_tasks", lazy=True))
