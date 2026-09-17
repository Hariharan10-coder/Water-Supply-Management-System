from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class Role:
    ADMIN = "admin"
    OFFICER = "officer"
    STAFF = "staff"
    CUSTOMER = "customer"

class User(UserMixin, db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(15), nullable=True)
    linked_customer_id = db.Column(db.Integer, db.ForeignKey("customers.customer_id"), nullable=True)
    zone = db.Column(db.String(50), nullable=True)
    is_active_account = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=False)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="user_account", uselist=False)

    def get_id(self):
        return str(self.user_id)

    @property
    def is_active(self):
        return self.is_active_account

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def has_role(self, *roles):
        return self.role in roles

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
