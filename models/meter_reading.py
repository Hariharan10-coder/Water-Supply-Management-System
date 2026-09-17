from datetime import datetime, date, timedelta
from extensions import db


def get_last_day_of_month(year, month):
    """Get last day of a given month"""
    if month == 12:
        return date(year, 12, 31)
    if month == 2:
        # Leap year check
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            return date(year, 2, 29)
        return date(year, 2, 28)
    if month in [4, 6, 9, 11]:
        return date(year, month, 30)
    return date(year, month, 31)


def calculate_next_reading_date(install_date):
    """
    Calculate next reading date - RULE:
    If install date <= 25th of month → end of SAME month
    If install date > 25th of month → end of NEXT month
    """
    if install_date.day <= 25:
        return get_last_day_of_month(install_date.year, install_date.month)
    else:
        next_month = install_date.month + 1
        next_year = install_date.year
        if next_month == 13:
            next_month = 1
            next_year += 1
        return get_last_day_of_month(next_year, next_month)


class MeterReading(db.Model):
    __tablename__ = "meter_readings"

    reading_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.customer_id"), nullable=False)
    previous_reading = db.Column(db.Float, default=0)
    current_reading = db.Column(db.Float, nullable=False)
    consumption = db.Column(db.Float, default=0)
    reading_date = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    is_abnormal = db.Column(db.Boolean, default=False)

    customer = db.relationship("Customer", backref=db.backref("readings", lazy=True))

    def calculate_consumption(self):
        self.consumption = self.current_reading - self.previous_reading


class MeterInstallation(db.Model):
    __tablename__ = "meter_installations"

    installation_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.customer_id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    install_date = db.Column(db.DateTime, nullable=True)
    initial_reading = db.Column(db.Float, default=0)
    meter_serial = db.Column(db.String(50), nullable=True)
    meter_type = db.Column(db.String(20), default="Digital")
    meter_status = db.Column(db.String(30), default="Assigned")  # Assigned, In Progress, Installed
    notes = db.Column(db.Text, nullable=True)

    customer = db.relationship("Customer", backref=db.backref("installation", uselist=False))
    staff = db.relationship("User", foreign_keys=[staff_id], backref=db.backref("installations", lazy=True))


class ReadingSchedule(db.Model):
    __tablename__ = "reading_schedules"

    schedule_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.customer_id"), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=True)
    scheduled_date = db.Column(db.Date, nullable=False)
    actual_reading_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="Pending")  # Pending, Completed, Missed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", backref=db.backref("schedules", lazy=True))
    staff = db.relationship("User", foreign_keys=[staff_id], backref=db.backref("schedules", lazy=True))
