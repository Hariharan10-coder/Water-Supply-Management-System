import re
from models import Customer, User

PHONE_PATTERN = re.compile(r"^\+?[0-9]{7,15}$")
METER_PATTERN = re.compile(r"^[A-Za-z0-9\-]{4,50}$")


def validate_customer_fields(name: str, address: str, phone: str, meter_no: str) -> list[str]:
    """
    Field-level checks for FR-2 / §8 Constraints:
    "Duplicate Customer IDs are not allowed", "Bills cannot be generated
    without meter readings" (enforced downstream), meter_no format, etc.
    Returns a list of error messages — empty list means valid.
    """
    errors = []

    if not name or not name.strip():
        errors.append("Customer name is required.")
    elif len(name.strip()) < 2:
        errors.append("Customer name is too short.")

    if not address or not address.strip():
        errors.append("Address is required.")

    if not phone or not PHONE_PATTERN.match(phone.strip()):
        errors.append("Enter a valid phone number (7–15 digits).")

    if not meter_no or not METER_PATTERN.match(meter_no.strip()):
        errors.append("Meter number must be 4–50 alphanumeric characters.")

    return errors


def check_duplicate_customer(phone: str, meter_no: str, exclude_customer_id: int = None) -> list[str]:
    """Enforces uniqueness on phone and meter_no (SRS §8 Constraints)."""
    errors = []

    phone_q = Customer.query.filter_by(phone=phone.strip())
    meter_q = Customer.query.filter_by(meter_no=meter_no.strip())
    if exclude_customer_id is not None:
        phone_q = phone_q.filter(Customer.customer_id != exclude_customer_id)
        meter_q = meter_q.filter(Customer.customer_id != exclude_customer_id)

    if phone_q.first() is not None:
        errors.append("This phone number is already registered.")
    if meter_q.first() is not None:
        errors.append("This meter number is already registered to another customer.")

    return errors


def username_available(username: str) -> bool:
    return User.query.filter_by(username=username.strip()).first() is None
