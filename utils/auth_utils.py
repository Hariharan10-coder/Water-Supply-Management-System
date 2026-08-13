import re

PASSWORD_MIN_LENGTH = 8


def password_meets_policy(raw_password: str) -> tuple[bool, str]:
    """
    Minimum complexity policy referenced in FR-9.
    Returns (is_valid, error_message).
    """
    if len(raw_password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters."
    if not re.search(r"[A-Za-z]", raw_password):
        return False, "Password must contain at least one letter."
    if not re.search(r"[0-9]", raw_password):
        return False, "Password must contain at least one number."
    return True, ""


def generate_temp_password() -> str:
    """
    Used when an Admin provisions an Officer/Staff account — the account is
    created with a temporary password and must_change_password=True, forcing
    a change on first login (SRS §8: no plaintext credentials persist).
    """
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(10))
