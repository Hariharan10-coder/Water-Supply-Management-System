from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from extensions import db
from models import User, Role, Customer, CustomerStatus
from services.notification_service import NotificationService
from utils.auth_utils import password_meets_policy
from utils.validators import validate_customer_fields, check_duplicate_customer, username_available, normalize_phone

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            if user.locked_until and user.locked_until > datetime.utcnow():
                flash("Account locked. Try again later.", "danger")
                return render_template("login.html")
            login_user(user)
            user.last_login = datetime.utcnow()
            user.failed_attempts = 0
            db.session.commit()
            if user.must_change_password:
                return redirect(url_for("auth.change_password"))
            return redirect(url_for("auth.dashboard"))
        else:
            if user:
                user.failed_attempts += 1
                if user.failed_attempts >= 5:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                db.session.commit()
            flash("Invalid username or password.", "danger")
    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        phone = normalize_phone(request.form.get("phone", ""))
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        zone = request.form.get("zone", "").strip()

        errors = validate_customer_fields(name, address, phone)
        errors += check_duplicate_customer(phone)

        if not username or len(username) < 4:
            errors.append("Username must be at least 4 characters.")
        elif not username_available(username):
            errors.append("That username is already taken.")

        ok, msg = password_meets_policy(password)
        if not ok:
            errors.append(msg)

        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", form=request.form)

        customer = Customer(
            name=name,
            address=address,
            phone=phone,
            meter_no=Customer.generate_meter_no(),
            zone=zone or None,
            status=CustomerStatus.PENDING
        )
        db.session.add(customer)
        db.session.flush()

        user = User(
            username=username,
            role=Role.CUSTOMER,
            linked_customer_id=customer.customer_id,
            phone=phone
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Notify all officers & admins
        NotificationService.send_to_officers_admins(
            "New Customer Registration",
            f"{name} registered. Meter: {customer.meter_no}",
            "registration",
            f"/customers/{customer.customer_id}/verify"
        )

        flash(f"Registration successful! Your Meter Number is {customer.meter_no}. Awaiting verification.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")



@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Customer self-service reset using username + registered phone number."""
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        phone = normalize_phone(request.form.get("phone", ""))
        user = User.query.filter_by(username=username).first()

        if user and user.role == Role.CUSTOMER and normalize_phone(user.phone) == phone:
            from flask import session
            session["password_reset_user_id"] = user.user_id
            return redirect(url_for("auth.reset_password"))

        flash("Customer account could not be verified with that username and phone number.", "danger")

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """Complete a verified customer password reset."""
    from flask import session

    user_id = session.get("password_reset_user_id")
    if not user_id:
        flash("Please start the password reset process again.", "warning")
        return redirect(url_for("auth.forgot_password"))

    user = db.session.get(User, user_id)
    if not user or user.role != Role.CUSTOMER:
        session.pop("password_reset_user_id", None)
        flash("Password reset session is no longer valid.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        ok, msg = password_meets_policy(new_password)

        if not ok:
            flash(msg, "danger")
        elif new_password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            user.set_password(new_password)
            user.must_change_password = False
            user.failed_attempts = 0
            user.locked_until = None
            db.session.commit()
            session.pop("password_reset_user_id", None)
            flash("Password reset successfully. You can now log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("reset_password.html", username=user.username)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role == Role.ADMIN:
        customers_count = Customer.query.count()
        pending_count = Customer.query.filter_by(status="Pending").count()
        pending_bills = 0
        return render_template("dashboard.html",
                               customers_count=customers_count,
                               pending_count=pending_count,
                               pending_bills=pending_bills)

    if current_user.role == Role.OFFICER:
        customers_count = Customer.query.count()
        pending_count = Customer.query.filter_by(status="Pending").count()
        pending_bills = 0
        return render_template("officer_dashboard.html",
                               customers_count=customers_count,
                               pending_count=pending_count,
                               pending_bills=pending_bills)

    if current_user.role == Role.STAFF:
        from models import MeterInstallation, ReadingSchedule
        installs = MeterInstallation.query.filter_by(staff_id=current_user.user_id, meter_status="Assigned").count()
        readings_due = ReadingSchedule.query.filter_by(staff_id=current_user.user_id, status="Pending").count()
        return render_template("maintenance_dashboard.html",
                               installs=installs,
                               readings_due=readings_due)

    if current_user.role == Role.CUSTOMER:
        customer = db.session.get(Customer, current_user.linked_customer_id) if current_user.linked_customer_id else None
        return render_template("customer_dashboard.html", customer=customer)

    return redirect(url_for("auth.logout"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old = request.form.get("current_password", "")
        new = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")
        if not current_user.check_password(old):
            flash("Current password incorrect.", "danger")
        else:
            ok, msg = password_meets_policy(new)
            if not ok:
                flash(msg, "danger")
            elif new != confirm:
                flash("New passwords do not match.", "danger")
            else:
                current_user.set_password(new)
                current_user.must_change_password = False
                db.session.commit()
                flash("Password changed successfully.", "success")
                return redirect(url_for("auth.dashboard"))
    return render_template("change_password.html")
