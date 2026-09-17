from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user

def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if not current_user.has_role(*roles):
                flash("Permission denied.", "danger")
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator
