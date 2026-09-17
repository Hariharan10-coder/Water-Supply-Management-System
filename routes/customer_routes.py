from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import User, Customer, Role, CustomerStatus, MeterInstallation, ReadingSchedule, calculate_next_reading_date
from services.notification_service import NotificationService
from services.rbac_service import roles_required
from utils.validators import normalize_phone, validate_customer_fields, check_duplicate_customer, username_available

customer_bp = Blueprint("customer", __name__, url_prefix="/customers")

ZONES = ["Zone 1 - North", "Zone 2 - South", "Zone 3 - East", "Zone 4 - West", "Zone 5 - Central"]


@customer_bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.OFFICER)
def list_customers():
    customers = Customer.query.order_by(Customer.customer_id.desc()).all()
    return render_template("customers/list.html", customers=customers)


@customer_bp.route("/<int:customer_id>/verify", methods=["GET", "POST"])
@login_required
@roles_required(Role.OFFICER, Role.ADMIN)
def verify_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":
        zone = request.form.get("zone", "").strip()
        staff_id = request.form.get("staff_id", type=int)
        notes = request.form.get("notes", "").strip()

        if not zone or not staff_id:
            flash("Please select zone and staff member.", "danger")
            return redirect(url_for("customer.verify_customer", customer_id=customer_id))

        # Update customer
        customer.status = CustomerStatus.ACTIVE
        customer.zone = zone
        customer.verified_at = datetime.utcnow()
        customer.verified_by = current_user.user_id

        # Create installation record
        installation = MeterInstallation(
            customer_id=customer_id,
            staff_id=staff_id,
            assigned_at=datetime.utcnow(),
            meter_status="Assigned",
            notes=notes
        )
        db.session.add(installation)
        db.session.commit()

        # Notify staff
        staff = db.session.get(User, staff_id)
        NotificationService.send(
            [staff_id],
            "New Installation Task",
            f"Install meter for {customer.name} at {customer.address}",
            "task",
            f"/installation/{installation.installation_id}"
        )

        # Notify customer
        NotificationService.send_to_customer(
            customer_id,
            "Account Verified",
            f"Your account is active. Staff will install your meter soon.",
            "success",
            "/dashboard"
        )

        flash(f"{customer.name} verified and installation assigned to {staff.username}.", "success")
        return redirect(url_for("customer.list_customers"))

    staff_members = User.query.filter_by(role=Role.STAFF).all()
    return render_template("customers/verify.html",
                           customer=customer,
                           staff_members=staff_members,
                           zones=ZONES)


@customer_bp.route("/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN)
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    user = customer.user_account

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        phone = normalize_phone(request.form.get("phone", ""))
        email = request.form.get("email", "").strip() or None
        username = request.form.get("username", "").strip()

        errors = validate_customer_fields(name, address, phone)
        errors += check_duplicate_customer(phone, exclude_id=customer.customer_id)

        if not username or len(username) < 4:
            errors.append("Username must be at least 4 characters.")
        elif user and not username_available(username, exclude_user_id=user.user_id):
            errors.append("That username is already taken.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("customers/edit.html", customer=customer, user=user, form=request.form)

        customer.name = name
        customer.address = address
        customer.phone = phone
        customer.email = email

        if user:
            user.username = username
            user.phone = phone
            user.email = email

        db.session.commit()
        flash("Customer account updated successfully.", "success")
        return redirect(url_for("customer.list_customers"))

    return render_template("customers/edit.html", customer=customer, user=user)


@customer_bp.route("/<int:customer_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    dependencies = {
        "bills": len(customer.bills),
        "readings": len(customer.readings),
        "maintenance requests": len(customer.maintenance_requests),
        "leakage reports": len(customer.leakage_reports),
        "reading schedules": len(customer.schedules),
        "meter installation": 1 if customer.installation else 0,
    }
    used_by = [f"{label}: {count}" for label, count in dependencies.items() if count]

    if used_by:
        flash(
            "Customer cannot be deleted because operational records exist (" +
            ", ".join(used_by) +
            "). Deactivate the customer account instead.",
            "warning"
        )
        return redirect(url_for("customer.list_customers"))

    user = customer.user_account
    if user:
        db.session.delete(user)
    db.session.delete(customer)
    db.session.commit()
    flash("Customer account deleted successfully.", "success")
    return redirect(url_for("customer.list_customers"))
