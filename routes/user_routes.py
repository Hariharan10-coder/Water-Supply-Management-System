import secrets
import string

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from extensions import db
from models import User, Role
from services.rbac_service import roles_required
from utils.auth_utils import password_meets_policy
from utils.validators import username_available, normalize_phone, validate_phone, check_duplicate_user_phone

user_bp = Blueprint("users", __name__, url_prefix="/users")


def generate_temporary_password(length=12):
    alphabet = string.ascii_letters + string.digits
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.isupper() for c in value)
                and any(c.islower() for c in value)
                and any(c.isdigit() for c in value)):
            return value


def staff_or_officer(user):
    return user.role in (Role.OFFICER, Role.STAFF)


@user_bp.route("/")
@login_required
@roles_required(Role.ADMIN)
def list_users():
    users = (User.query
             .filter(User.role.in_([Role.OFFICER, Role.STAFF]))
             .order_by(User.user_id.desc()).all())
    return render_template("users/list.html", users=users)


@user_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN)
def create_user():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        phone = normalize_phone(request.form.get("phone", ""))
        email = request.form.get("email", "").strip() or None
        role = request.form.get("role", "")
        password = request.form.get("password", "")

        errors = []
        if not full_name or len(full_name) < 2:
            errors.append("Full Name is required.")
        if not username or len(username) < 4:
            errors.append("Username must be at least 4 characters.")
        elif not username_available(username):
            errors.append("That username is already taken.")
        if not validate_phone(phone):
            errors.append("Valid phone number required (7-15 digits).")
        else:
            errors += check_duplicate_user_phone(phone)
        if role not in (Role.OFFICER, Role.STAFF):
            errors.append("Select Water Supply Officer or Maintenance Staff.")
        ok, msg = password_meets_policy(password)
        if not ok:
            errors.append(msg)

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("users/new.html", form=request.form)

        user = User(full_name=full_name, username=username, role=role,
                    email=email, phone=phone, is_active_account=True,
                    must_change_password=False)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        label = "Water Supply Officer" if role == Role.OFFICER else "Maintenance Staff"
        flash(f"{label} account created for {full_name}.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/new.html")


@user_bp.route("/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN)
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if not staff_or_officer(user):
        flash("Only Officer and Maintenance Staff accounts can be managed here.", "danger")
        return redirect(url_for("users.list_users"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        phone = normalize_phone(request.form.get("phone", ""))
        email = request.form.get("email", "").strip() or None

        errors = []
        if not full_name or len(full_name) < 2:
            errors.append("Full Name is required.")
        if not username or len(username) < 4:
            errors.append("Username must be at least 4 characters.")
        elif not username_available(username, exclude_user_id=user.user_id):
            errors.append("That username is already taken.")
        if not validate_phone(phone):
            errors.append("Valid phone number required (7-15 digits).")
        else:
            errors += check_duplicate_user_phone(phone, exclude_user_id=user.user_id)

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("users/edit.html", user=user, form=request.form)

        user.full_name = full_name
        user.username = username
        user.phone = phone
        user.email = email
        db.session.commit()
        flash("Account updated successfully.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/edit.html", user=user)


@user_bp.route("/<int:user_id>/reset-password", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    if not staff_or_officer(user):
        flash("Only Officer and Maintenance Staff accounts can be reset here.", "danger")
        return redirect(url_for("users.list_users"))

    temporary_password = generate_temporary_password()
    user.set_password(temporary_password)
    user.must_change_password = True
    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit()

    return render_template("users/temp_password.html",
                           user=user, temporary_password=temporary_password)


@user_bp.route("/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if not staff_or_officer(user):
        flash("Only Officer and Maintenance Staff accounts can be activated/deactivated here.", "danger")
        return redirect(url_for("users.list_users"))

    user.is_active_account = not user.is_active_account
    db.session.commit()
    state = "activated" if user.is_active_account else "deactivated"
    flash(f"{user.username} account {state}.", "success")
    return redirect(url_for("users.list_users"))
