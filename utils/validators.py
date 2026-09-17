import re
from models import Customer, User


def normalize_phone(phone):
    return re.sub(r"\s+", "", (phone or "").strip())


def validate_phone(phone):
    phone = normalize_phone(phone)
    return bool(phone and re.fullmatch(r"[+]?\d{7,15}", phone))


def validate_customer_fields(name, address, phone):
    errors = []
    if not name or len(name.strip()) < 2:
        errors.append("Name is required (min 2 chars).")
    if not address or len(address.strip()) < 3:
        errors.append("Address is required.")
    if not validate_phone(phone):
        errors.append("Valid phone number required (7-15 digits).")
    return errors


def check_duplicate_customer(phone, exclude_id=None):
    phone = normalize_phone(phone)
    q = Customer.query.filter_by(phone=phone)
    if exclude_id:
        q = q.filter(Customer.customer_id != exclude_id)
    if q.first():
        return ["Phone number already registered."]
    return []


def username_available(username, exclude_user_id=None):
    q = User.query.filter_by(username=username.strip())
    if exclude_user_id:
        q = q.filter(User.user_id != exclude_user_id)
    return q.first() is None


def check_duplicate_user_phone(phone, exclude_user_id=None):
    phone = normalize_phone(phone)
    if not phone:
        return []
    q = User.query.filter_by(phone=phone)
    if exclude_user_id:
        q = q.filter(User.user_id != exclude_user_id)
    if q.first():
        return ["Phone number is already used by another account."]
    return []
