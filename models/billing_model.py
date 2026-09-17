from datetime import datetime, timedelta

from extensions import db


class BillingStatus:
    PENDING = "Pending"
    PAID = "Paid"
    OVERDUE = "Overdue"
    DISPUTED = "Disputed"


class Bill(db.Model):
    __tablename__ = "bills"

    bill_id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.customer_id"),
        nullable=False
    )

    meter_reading_id = db.Column(
        db.Integer,
        db.ForeignKey("meter_readings.reading_id"),
        nullable=True
    )

    units_consumed = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    rate_per_unit = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    amount = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    late_fee = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    total_amount = db.Column(
        db.Float,
        nullable=False,
        default=0.0
    )

    bill_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    due_date = db.Column(
        db.Date,
        nullable=False
    )

    paid_at = db.Column(
        db.DateTime,
        nullable=True
    )

    payment_reference = db.Column(
        db.String(100),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        default=BillingStatus.PENDING
    )

    generated_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=True
    )

    # Relationships
    customer = db.relationship(
        "Customer",
        backref=db.backref("bills", lazy=True)
    )

    # ---------------------------------------------------------
    # Calculate the final bill amount
    # ---------------------------------------------------------
    def calculate_total(self):
        """
        Calculate total bill amount safely.

        This prevents:
            float + NoneType

        if amount or late_fee happens to be NULL/None.
        """

        amount = self.amount if self.amount is not None else 0.0
        late_fee = self.late_fee if self.late_fee is not None else 0.0

        self.total_amount = amount + late_fee

        return self.total_amount

    # ---------------------------------------------------------
    # Calculate bill amount from units and rate
    # ---------------------------------------------------------
    def calculate_amount(self):
        """
        Calculate the basic bill amount from:

            units_consumed × rate_per_unit
        """

        units = (
            self.units_consumed
            if self.units_consumed is not None
            else 0.0
        )

        rate = (
            self.rate_per_unit
            if self.rate_per_unit is not None
            else 0.0
        )

        self.amount = units * rate

        # Make sure late fee is never None
        if self.late_fee is None:
            self.late_fee = 0.0

        self.calculate_total()

        return self.amount

    # ---------------------------------------------------------
    # Apply late fee
    # ---------------------------------------------------------
    def apply_late_fee(self):
        """
        Apply late payment charges.

        1–15 days late   → ₹50
        16–30 days late  → ₹100
        More than 30     → ₹200
        """

        # If there is no due date, do nothing
        if self.due_date is None:
            if self.late_fee is None:
                self.late_fee = 0.0

            self.calculate_total()
            return self.total_amount

        today = datetime.utcnow().date()

        # No late fee if bill is not overdue
        if today <= self.due_date:
            if self.late_fee is None:
                self.late_fee = 0.0

            self.calculate_total()
            return self.total_amount

        # Don't charge late fee after payment
        if self.status == BillingStatus.PAID:
            if self.late_fee is None:
                self.late_fee = 0.0

            self.calculate_total()
            return self.total_amount

        days_late = (today - self.due_date).days

        if days_late <= 15:
            self.late_fee = 50.0

        elif days_late <= 30:
            self.late_fee = 100.0

        else:
            self.late_fee = 200.0

        self.status = BillingStatus.OVERDUE

        self.calculate_total()

        return self.total_amount

    # ---------------------------------------------------------
    # Default due date
    # ---------------------------------------------------------
    @classmethod
    def default_due_date(cls, days=15):
        """
        Return a due date 'days' days from today.
        """

        return datetime.utcnow().date() + timedelta(days=days)

    # ---------------------------------------------------------
    # Mark bill as paid
    # ---------------------------------------------------------
    def mark_as_paid(self, payment_reference=None):
        """
        Mark the bill as paid.
        """

        self.status = BillingStatus.PAID
        self.paid_at = datetime.utcnow()

        if payment_reference:
            self.payment_reference = payment_reference

        # Keep existing late fee but make sure it isn't None
        if self.late_fee is None:
            self.late_fee = 0.0

        self.calculate_total()

    # ---------------------------------------------------------
    # Check whether bill is overdue
    # ---------------------------------------------------------
    def is_overdue(self):
        """
        Return True if the bill is overdue and unpaid.
        """

        if self.due_date is None:
            return False

        if self.status == BillingStatus.PAID:
            return False

        return datetime.utcnow().date() > self.due_date

    # ---------------------------------------------------------
    # String representation
    # ---------------------------------------------------------
    def __repr__(self):
        return (
            f"<Bill {self.bill_id} "
            f"Customer={self.customer_id} "
            f"Amount={self.total_amount}>"
        )