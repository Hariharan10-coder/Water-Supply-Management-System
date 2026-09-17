from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from extensions import db
from models import MeterReading, Customer, Role, ReadingSchedule
from services.rbac_service import roles_required

meter_bp = Blueprint("meter", __name__, url_prefix="/meter")


@meter_bp.route("/")
@login_required
@roles_required(Role.ADMIN, Role.OFFICER, Role.CUSTOMER)
def list_readings():
    if current_user.role == Role.CUSTOMER:
        readings = MeterReading.query.filter_by(
            customer_id=current_user.linked_customer_id
        ).order_by(MeterReading.reading_date.desc()).all()
    else:
        readings = MeterReading.query.order_by(MeterReading.reading_date.desc()).all()
    return render_template("meters/list.html", readings=readings)
