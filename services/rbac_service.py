"""
Role-based access control. Implements the matrix in SRS §8.1:

  Function                    | Admin | Officer | Staff | Customer
  ---------------------------- ------- --------- ------- ----------
  Manage customers            | Full  | View    | None  | None
  Record meter readings       | None  | Full    | None  | None
  Generate bills               | View  | Full    | None  | View own
  Update maintenance status   | View  | View    | Full  | Submit/own
  Update leakage status       | View  | View    | Full  | Submit/own
  Manage complaints           |Assign | None    |Update | Submit/own
  Generate reports            | Full  | Limited | None  | None

Every route that touches these functions is wrapped with @roles_required(...)
so a role can never reach a function outside its row — this is what FR
acceptance testing (§9) checks against.
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def roles_required(*allowed_roles):
    """Restrict a view to the given roles. Use on top of @login_required."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if not current_user.has_role(*allowed_roles):
                flash("You don't have permission to access that page.", "danger")
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator


def can_edit_customers(user) -> bool:
    """Admin: full edit. Officer: view only (used to toggle UI controls)."""
    return user.has_role("admin")


def can_view_customers(user) -> bool:
    return user.has_role("admin", "officer")
