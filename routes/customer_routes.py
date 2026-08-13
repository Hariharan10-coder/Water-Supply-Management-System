from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from extensions import db
from models import Customer, Role, CustomerStatus
from services.rbac_service import roles_required, can_edit_customers
from utils.validators import validate_customer_fields, check_duplicate_customer

customer_bp = Blueprint("customer", __name__, url_prefix="/customers")


@customer_bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.OFFICER)
def list_customers():
    """Admin: full control. Officer: view only (§8.1 matrix)."""
    query = request.args.get("q", "").strip()
    q = Customer.query
    if query:
        like = f"%{query}%"
        q = q.filter(
            db.or_(
                Customer.name.ilike(like),
                Customer.phone.ilike(like),
                Customer.meter_no.ilike(like),
            )
        )
    customers = q.order_by(Customer.customer_id.desc()).all()
    return render_template(
        "customers/list.html",
        customers=customers,
        query=query,
        can_edit=can_edit_customers(current_user),
    )


@customer_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN)
def add_customer():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        meter_no = request.form.get("meter_no", "").strip()

        errors = validate_customer_fields(name, address, phone, meter_no)
        errors += check_duplicate_customer(phone, meter_no)

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("customers/form.html", form=request.form, mode="add"), 400

        customer = Customer(
            name=name, address=address, phone=phone,
            meter_no=meter_no, status=CustomerStatus.ACTIVE,
        )
        db.session.add(customer)
        db.session.commit()
        flash(f"Customer '{name}' added.", "success")
        return redirect(url_for("customer.list_customers"))

    return render_template("customers/form.html", form={}, mode="add")


@customer_bp.route("/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN)
def edit_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        meter_no = request.form.get("meter_no", "").strip()

        errors = validate_customer_fields(name, address, phone, meter_no)
        errors += check_duplicate_customer(phone, meter_no, exclude_customer_id=customer_id)

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("customers/form.html", form=request.form, mode="edit", customer=customer), 400

        customer.name, customer.address = name, address
        customer.phone, customer.meter_no = phone, meter_no
        db.session.commit()
        flash(f"Customer '{name}' updated.", "success")
        return redirect(url_for("customer.list_customers"))

    return render_template("customers/form.html", form=customer.__dict__, mode="edit", customer=customer)


@customer_bp.route("/<int:customer_id>/delete", methods=["POST"])
@login_required
@roles_required(Role.ADMIN)
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    name = customer.name
    db.session.delete(customer)
    db.session.commit()
    flash(f"Customer '{name}' deleted.", "info")
    return redirect(url_for("customer.list_customers"))


@customer_bp.route("/<int:customer_id>/verify", methods=["POST"])
@login_required
@roles_required(Role.OFFICER, Role.ADMIN)
def verify_customer(customer_id):
    """Officer confirms a self-registered customer's meter number is genuine."""
    customer = Customer.query.get_or_404(customer_id)
    customer.status = CustomerStatus.ACTIVE
    db.session.commit()
    flash(f"Customer '{customer.name}' verified and activated.", "success")
    return redirect(url_for("customer.list_customers"))
