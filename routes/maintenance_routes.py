from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import MaintenanceRequest, Customer, Role, User, MaintenanceStatus
from services.notification_service import NotificationService
from services.rbac_service import roles_required

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/maintenance")


@maintenance_bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.STAFF, Role.CUSTOMER)
def list_requests():
    if current_user.role == Role.CUSTOMER:
        requests = MaintenanceRequest.query.filter_by(customer_id=current_user.linked_customer_id).order_by(MaintenanceRequest.created_at.desc()).all()
    elif current_user.role == Role.STAFF:
        requests = MaintenanceRequest.query.filter_by(assigned_to=current_user.user_id).order_by(MaintenanceRequest.created_at.desc()).all()
    else:
        requests = MaintenanceRequest.query.order_by(MaintenanceRequest.created_at.desc()).all()

    from models import User as U
    staff_members = U.query.filter_by(role=Role.STAFF).all()
    return render_template("maintenance/list.html", requests=requests, maintenance_staff=staff_members)


@maintenance_bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.CUSTOMER, Role.STAFF)
def create_request():
    if request.method == "POST":
        issue = request.form.get("issue_type", "").strip()
        desc = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")

        if not issue or not desc:
            flash("All fields required.", "danger")
            return redirect(url_for("maintenance.create_request"))

        cid = current_user.linked_customer_id
        if current_user.has_role(Role.ADMIN, Role.OFFICER, Role.STAFF):
            cid = request.form.get("customer_id", type=int)

        item = MaintenanceRequest(
            customer_id=cid,
            issue_type=issue,
            description=desc,
            priority=priority
        )
        db.session.add(item)
        db.session.commit()

        NotificationService.send_to_officers_admins(
            "New Maintenance Request",
            f"Issue: {issue} - Priority: {priority}",
            "maintenance",
            f"/maintenance/"
        )

        flash("Request created.", "success")
        return redirect(url_for("maintenance.list_requests"))

    customers = Customer.query.all() if current_user.has_role(Role.ADMIN, Role.OFFICER, Role.STAFF) else None
    return render_template("maintenance/form.html", customers=customers)


@maintenance_bp.route("/<int:request_id>/assign", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.OFFICER)
def assign_request(request_id):
    item = MaintenanceRequest.query.get_or_404(request_id)
    staff_id = request.form.get("staff_id", type=int)

    if not staff_id:
        flash("Select a staff member.", "danger")
        return redirect(url_for("maintenance.list_requests"))

    item.assigned_to = staff_id
    item.status = MaintenanceStatus.ASSIGNED
    db.session.commit()

    staff = db.session.get(User, staff_id)
    NotificationService.send(
        [staff_id],
        "New Task Assigned",
        f"Maintenance Request #{request_id}",
        "task",
        f"/maintenance/"
    )

    flash(f"Assigned to {staff.username}.", "success")
    return redirect(url_for("maintenance.list_requests"))


@maintenance_bp.route("/<int:request_id>/status", methods=["POST"])
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.STAFF)
def update_status(request_id):
    item = MaintenanceRequest.query.get_or_404(request_id)
    new_status = request.form.get("status", "")

    item.status = new_status
    if new_status == "Completed":
        from datetime import datetime
        item.resolved_at = datetime.utcnow()
    db.session.commit()

    flash(f"Status updated to {new_status}.", "success")
    return redirect(url_for("maintenance.list_requests"))
