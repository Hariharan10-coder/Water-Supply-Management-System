from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from services.notification_service import NotificationService

notification_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notification_bp.route("/")
@login_required
def view_all():
    notifications = NotificationService.get_all(current_user.user_id)
    return render_template("notifications/view.html", notifications=notifications)


@notification_bp.route("/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    NotificationService.mark_all_read(current_user.user_id)
    flash("All marked as read.", "success")
    return redirect(url_for("notifications.view_all"))


@notification_bp.route("/<int:nid>/read", methods=["POST"])
@login_required
def mark_read(nid):
    NotificationService.mark_read(nid)
    return redirect(url_for("notifications.view_all"))
