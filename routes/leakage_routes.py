from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import LeakageReport, Customer, Role, User, LeakageStatus
from services.notification_service import NotificationService
from services.rbac_service import roles_required

leakage_bp = Blueprint("leakage", __name__, url_prefix="/leakage")


@leakage_bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.STAFF, Role.CUSTOMER)
def list_reports():
    if current_user.role == Role.CUSTOMER:
        reports = LeakageReport.query.filter_by(customer_id=current_user.linked_customer_id).order_by(LeakageReport.created_at.desc()).all()
    elif current_user.role == Role.STAFF:
        reports = LeakageReport.query.filter_by(assigned_to=current_user.user_id).order_by(LeakageReport.created_at.desc()).all()
    else:
        reports = LeakageReport.query.order_by(LeakageReport.created_at.desc()).all()

    staff_members = User.query.filter_by(role=Role.STAFF).all()
    return render_template("leakage/list.html", reports=reports, maintenance_staff=staff_members)


@leakage_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.STAFF, Role.CUSTOMER)
def create_report():
    if request.method == "POST":
        location = request.form.get("location", "").strip()
        desc = request.form.get("description", "").strip()
        severity = request.form.get("severity", "Medium")

        if not location or not desc:
            flash("All fields required.", "danger")
            return redirect(url_for("leakage.create_report"))

        cid = current_user.linked_customer_id
        if current_user.has_role(Role.ADMIN, Role.OFFICER, Role.STAFF):
            cid = request.form.get("customer_id", type=int)

        report = LeakageReport(
            customer_id=cid,
            location=location,
            description=desc,
            severity=severity,
            reported_by=current_user.user_id
        )
        db.session.add(report)
        db.session.commit()

        NotificationService.send_to_officers_admins(
            "New Leakage Report",
            f"{location} - {severity}",
            "leakage",
            f"/leakage/"
        )

        flash("Leakage reported.", "success")
        return redirect(url_for("leakage.list_reports"))

    customers = Customer.query.all() if current_user.has_role(Role.ADMIN, Role.OFFICER, Role.STAFF) else None
    return render_template("leakage/form.html", customers=customers)


@leakage_bp.route("/<int:report_id>/assign", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.OFFICER)
def assign_report(report_id):
    report = LeakageReport.query.get_or_404(report_id)
    staff_id = request.form.get("staff_id", type=int)

    if not staff_id:
        flash("Select a staff member.", "danger")
        return redirect(url_for("leakage.list_reports"))

    report.assigned_to = staff_id
    report.status = LeakageStatus.ASSIGNED
    db.session.commit()

    staff = db.session.get(User, staff_id)
    NotificationService.send(
        [staff_id],
        "New Leakage Task",
        f"Leakage at {report.location}",
        "task",
        f"/leakage/"
    )

    flash(f"Assigned to {staff.username}.", "success")
    return redirect(url_for("leakage.list_reports"))


@leakage_bp.route("/<int:report_id>/status", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.STAFF)
def update_status(report_id):
    report = LeakageReport.query.get_or_404(report_id)
    new_status = request.form.get("status", "")

    report.status = new_status
    if new_status in ["Resolved", "Closed"]:
        from datetime import datetime
        report.resolved_at = datetime.utcnow()
    db.session.commit()

    flash(f"Status updated to {new_status}.", "success")
    return redirect(url_for("leakage.list_reports"))
