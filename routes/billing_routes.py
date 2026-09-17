from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Bill, BillingStatus, Customer, MeterReading, Role
from services.notification_service import NotificationService
from services.rbac_service import roles_required
from datetime import datetime, timedelta

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.route("/")
@login_required
def list_bills():
    if current_user.role == Role.CUSTOMER:
        bills = Bill.query.filter_by(customer_id=current_user.linked_customer_id).all()
    else:
        bills = Bill.query.all()
    for b in bills:
        b.apply_late_fee()
    db.session.commit()
    return render_template("billing/list.html", bills=bills)


@billing_bp.route("/generate", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.OFFICER)
def generate_bill():
    customers = Customer.query.filter_by(status="Active").all()
    if request.method == "POST":
        customer_id = request.form.get("customer_id", type=int)
        rate = request.form.get("rate", type=float)
        reading = MeterReading.query.filter_by(customer_id=customer_id).order_by(MeterReading.reading_date.desc()).first()
        if not reading:
            flash("No reading found for this customer.", "danger")
            return redirect(url_for("billing.generate_bill"))

        bill = Bill(
            customer_id=customer_id,
            meter_reading_id=reading.reading_id,
            units_consumed=reading.consumption,
            rate_per_unit=rate,
            amount=reading.consumption * rate,
            due_date=Bill.default_due_date(15),
            generated_by=current_user.user_id
        )
        bill.calculate_total()
        db.session.add(bill)
        db.session.commit()

        NotificationService.send_to_customer(
            customer_id,
            "New Bill Generated",
            f"Bill #{bill.bill_id}: ₹{bill.total_amount} - Due: {bill.due_date.strftime('%d/%m/%Y')}",
            "billing",
            "/billing/"
        )

        flash(f"Bill #{bill.bill_id} generated.", "success")
        return redirect(url_for("billing.list_bills"))
    return render_template("billing/form.html", customers=customers)


@billing_bp.route("/<int:bill_id>/pay", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.CUSTOMER)
def pay_bill(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    if current_user.role == Role.CUSTOMER and current_user.linked_customer_id != bill.customer_id:
        flash("Access denied.", "danger")
        return redirect(url_for("billing.list_bills"))

    ref = request.form.get("reference", "").strip()

    bill.status = BillingStatus.PAID
    bill.paid_at = datetime.utcnow()
    bill.late_fee = 0
    bill.payment_reference = ref
    bill.calculate_total()
    db.session.commit()

    NotificationService.send_to_customer(
        bill.customer_id,
        "Payment Confirmed",
        f"Bill #{bill.bill_id} paid: ₹{bill.total_amount}",
        "payment",
        "/billing/"
    )

    flash(f"Bill #{bill.bill_id} marked as paid.", "success")
    return redirect(url_for("billing.list_bills"))
