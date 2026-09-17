from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import MeterInstallation, Customer, Role, ReadingSchedule, MeterReading, calculate_next_reading_date
from services.notification_service import NotificationService
from services.rbac_service import roles_required

installation_bp = Blueprint("installation", __name__, url_prefix="/installation")


@installation_bp.route("/list")
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.STAFF)
def list_installations():
    if current_user.role == Role.STAFF:
        installs = MeterInstallation.query.filter_by(staff_id=current_user.user_id).order_by(MeterInstallation.assigned_at.desc()).all()
    else:
        installs = MeterInstallation.query.order_by(MeterInstallation.assigned_at.desc()).all()
    return render_template("installation/list.html", installations=installs)


@installation_bp.route("/<int:installation_id>", methods=["GET", "POST"])
@login_required
@roles_required(Role.STAFF, Role.ADMIN, Role.OFFICER)
def complete_installation(installation_id):
    installation = MeterInstallation.query.get_or_404(installation_id)

    if current_user.role == Role.STAFF and installation.staff_id != current_user.user_id:
        flash("Not your task.", "danger")
        return redirect(url_for("installation.list_installations"))

    if request.method == "POST":
        initial_reading = request.form.get("initial_reading", type=float)
        meter_serial = request.form.get("meter_serial", "").strip()
        meter_type = request.form.get("meter_type", "Digital")

        if initial_reading is None:
            flash("Initial reading required.", "danger")
            return redirect(url_for("installation.complete_installation", installation_id=installation_id))

        # Update installation
        installation.install_date = datetime.utcnow()
        installation.initial_reading = initial_reading
        installation.meter_serial = meter_serial
        installation.meter_type = meter_type
        installation.meter_status = "Installed"

        # Create first meter reading
        reading = MeterReading(
            customer_id=installation.customer_id,
            previous_reading=0,
            current_reading=initial_reading,
            consumption=initial_reading,
            recorded_by=current_user.user_id
        )
        reading.calculate_consumption()
        db.session.add(reading)

        # Create reading schedule
        next_date = calculate_next_reading_date(installation.install_date.date())
        schedule = ReadingSchedule(
            customer_id=installation.customer_id,
            staff_id=installation.staff_id,
            scheduled_date=next_date,
            status="Pending"
        )
        db.session.add(schedule)
        db.session.commit()

        # Notifications
        NotificationService.send_to_officers_admins(
            "Meter Installed",
            f"Meter installed for {installation.customer.name}",
            "installation",
            f"/installation/list"
        )
        NotificationService.send_to_customer(
            installation.customer_id,
            "Meter Installed Successfully",
            f"Your meter is active. Next reading: {next_date.strftime('%d/%m/%Y')}",
            "success",
            "/dashboard"
        )
        NotificationService.send(
            [installation.staff_id],
            "Next Reading Scheduled",
            f"Reading for {installation.customer.name} due: {next_date.strftime('%d/%m/%Y')}",
            "reading",
            "/installation/readings"
        )

        flash(f"Meter installed! Initial reading: {initial_reading}", "success")
        return redirect(url_for("installation.list_installations"))

    return render_template("installation/complete.html", installation=installation)


@installation_bp.route("/readings")
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.STAFF)
def readings():
    if current_user.role == Role.STAFF:
        schedules = ReadingSchedule.query.filter_by(staff_id=current_user.user_id).order_by(ReadingSchedule.scheduled_date.asc()).all()
    else:
        schedules = ReadingSchedule.query.order_by(ReadingSchedule.scheduled_date.asc()).all()
    return render_template("installation/readings.html", schedules=schedules)


@installation_bp.route("/readings/<int:schedule_id>/record", methods=["POST"])
@login_required
@roles_required(Role.STAFF, Role.ADMIN, Role.OFFICER)
def record_reading(schedule_id):
    schedule = ReadingSchedule.query.get_or_404(schedule_id)
    current_value = request.form.get("reading", type=float)

    if current_value is None:
        flash("Reading required.", "danger")
        return redirect(url_for("installation.readings"))

    prev = MeterReading.query.filter_by(
        customer_id=schedule.customer_id
    ).order_by(MeterReading.reading_date.desc()).first()
    prev_value = prev.current_reading if prev else 0

    if current_value < prev_value:
        flash("Reading cannot be lower than previous.", "danger")
        return redirect(url_for("installation.readings"))

    # Create reading
    reading = MeterReading(
        customer_id=schedule.customer_id,
        previous_reading=prev_value,
        current_reading=current_value,
        recorded_by=current_user.user_id
    )
    reading.calculate_consumption()
    db.session.add(reading)

    # Mark schedule completed
    schedule.status = "Completed"
    schedule.actual_reading_date = datetime.utcnow()

    # Create next schedule
    next_date = calculate_next_reading_date(datetime.utcnow().date())
    next_schedule = ReadingSchedule(
        customer_id=schedule.customer_id,
        staff_id=schedule.staff_id,
        scheduled_date=next_date,
        status="Pending"
    )
    db.session.add(next_schedule)
    db.session.commit()

    # Notify officers
    NotificationService.send_to_officers_admins(
        "Reading Completed",
        f"{schedule.customer.name}: {reading.consumption} units. Ready for billing.",
        "reading",
        f"/billing/generate"
    )

    flash(f"Reading recorded: {reading.consumption} units.", "success")
    return redirect(url_for("installation.readings"))
