from datetime import datetime, UTC
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class Role:
    """Fixed role vocabulary — matches the RBAC matrix in SRS §8.1."""
    ADMIN = "admin"
    OFFICER = "officer"
    STAFF = "staff"
    CUSTOMER = "customer"

    ALL = (ADMIN, OFFICER, STAFF, CUSTOMER)
    STAFF_SIDE = (ADMIN, OFFICER, STAFF)  # roles an Admin provisions manually


class User(UserMixin, db.Model):
    """
    Login identity for every role. SRS §7.7.

    Registration differs by role (see auth_routes.py / admin routes):
      - CUSTOMER: self-registers via the public form, linked to a Customer row.
      - ADMIN / OFFICER / STAFF: created only by an existing Admin — there is
        no public signup path for these roles (SRS §8, security control).
    """
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # Only populated when role == CUSTOMER
    linked_customer_id = db.Column(
        db.Integer, db.ForeignKey("customers.customer_id"), nullable=True
    )

    # Account lifecycle
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    must_change_password = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    customer = db.relationship("Customer", back_populates="user_account", uselist=False)

    # --- Flask-Login required property ---
    def get_id(self):
        return str(self.user_id)

    @property
    def is_active(self):
        return self.is_active_account

    # --- Password handling (SRS §8.2 — salted hash, never plaintext) ---
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # --- Role helpers ---
    def has_role(self, *roles) -> bool:
        return self.role in roles

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
