from datetime import datetime
from extensions import db

class LeakageStatus:
    REPORTED = "Reported"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class LeakageSeverity:
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class LeakageReport(db.Model):
    __tablename__ = "leakage_reports"

    report_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.customer_id"), nullable=True)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default=LeakageSeverity.MEDIUM)
    status = db.Column(db.String(20), default=LeakageStatus.REPORTED)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    reported_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    customer = db.relationship("Customer", backref=db.backref("leakage_reports", lazy=True))
    assignee = db.relationship("User", foreign_keys=[assigned_to], backref=db.backref("leakage_tasks", lazy=True))
