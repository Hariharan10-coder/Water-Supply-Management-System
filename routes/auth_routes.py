"""
Authentication and account management routes.

Registration deliberately differs by role:

Customer
-> Public self-service registration (/register)

Officer / Maintenance Staff
-> Created only by an Admin (/users/new)

Admin
-> Seeded once via seed_admin.py or promoted by an existing Admin
Never through a public registration form.

Dashboards:
Admin
-> dashboard.html

Officer
-> officer_dashboard.html

Maintenance Staff
-> maintenance_dashboard.html

Customer
-> customer_dashboard.html
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from extensions import db

from models import (
    User,
    Role,
    Customer,
    CustomerStatus,
)

from services.rbac_service import roles_required

from utils.auth_utils import (
    password_meets_policy,
    generate_temp_password,
)

from utils.validators import (
    validate_customer_fields,
    check_duplicate_customer,
    username_available,
)


# ================================================================
# Blueprint
# ================================================================

auth_bp = Blueprint(
    "auth",
    __name__
)


# ================================================================
# Home
# ================================================================

@auth_bp.route("/", methods=["GET"])
def index():

    if current_user.is_authenticated:

        return redirect(
            url_for("auth.dashboard")
        )

    return redirect(
        url_for("auth.login")
    )


# ================================================================
# Login
# ================================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # ------------------------------------------------------------
    # Already logged in
    # ------------------------------------------------------------

    if current_user.is_authenticated:

        return redirect(
            url_for("auth.dashboard")
        )

    # ------------------------------------------------------------
    # POST
    # ------------------------------------------------------------

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # --------------------------------------------------------
        # Find user
        # --------------------------------------------------------

        user = User.query.filter_by(
            username=username
        ).first()

        # --------------------------------------------------------
        # Invalid username/password
        # --------------------------------------------------------

        if user is None or not user.check_password(password):

            flash(
                "Invalid username or password.",
                "danger"
            )

            return render_template(
                "login.html"
            ), 401

        # --------------------------------------------------------
        # Check account status
        # --------------------------------------------------------

        if not user.is_active_account:

            flash(
                "This account has been deactivated. "
                "Contact an administrator.",
                "danger"
            )

            return render_template(
                "login.html"
            ), 403

        # --------------------------------------------------------
        # Login
        # --------------------------------------------------------

        login_user(user)

        # --------------------------------------------------------
        # Temporary password
        # --------------------------------------------------------

        if user.must_change_password:

            flash(
                "Please set a new password before continuing.",
                "warning"
            )

            return redirect(
                url_for("auth.change_password")
            )

        # --------------------------------------------------------
        # Normal login
        # --------------------------------------------------------

        flash(
            f"Welcome back, {user.username}.",
            "success"
        )

        return redirect(
            url_for("auth.dashboard")
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    return render_template(
        "login.html"
    )


# ================================================================
# Logout
# ================================================================

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You've been logged out.",
        "info"
    )

    return redirect(
        url_for("auth.login")
    )


# ================================================================
# Customer Registration
# ================================================================

@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register_customer():

    """
    Public signup — CUSTOMER role only.
    """

    # ------------------------------------------------------------
    # POST
    # ------------------------------------------------------------

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        meter_no = request.form.get(
            "meter_no",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm = request.form.get(
            "confirm_password",
            ""
        )

        # --------------------------------------------------------
        # Validate customer information
        # --------------------------------------------------------

        errors = validate_customer_fields(
            name,
            address,
            phone,
            meter_no
        )

        errors += check_duplicate_customer(
            phone,
            meter_no
        )

        # --------------------------------------------------------
        # Validate username
        # --------------------------------------------------------

        if not username or len(username) < 4:

            errors.append(
                "Username must be at least 4 characters."
            )

        elif not username_available(username):

            errors.append(
                "That username is already taken."
            )

        # --------------------------------------------------------
        # Validate password
        # --------------------------------------------------------

        ok, msg = password_meets_policy(
            password
        )

        if not ok:

            errors.append(msg)

        if password != confirm:

            errors.append(
                "Passwords do not match."
            )

        # --------------------------------------------------------
        # Display errors
        # --------------------------------------------------------

        if errors:

            for error in errors:

                flash(
                    error,
                    "danger"
                )

            return render_template(
                "register.html",
                form=request.form
            ), 400

        # --------------------------------------------------------
        # Create Customer
        # --------------------------------------------------------

        customer = Customer(
            name=name,
            address=address,
            phone=phone,
            meter_no=meter_no,
            status=CustomerStatus.PENDING,
        )

        db.session.add(customer)

        # Get customer ID
        db.session.flush()

        # --------------------------------------------------------
        # Create linked User
        # --------------------------------------------------------

        user = User(
            username=username,
            role=Role.CUSTOMER,
            linked_customer_id=customer.customer_id
        )

        user.set_password(
            password
        )

        db.session.add(user)

        db.session.commit()

        # --------------------------------------------------------
        # Success
        # --------------------------------------------------------

        flash(
            "Registration submitted. "
            "Your account is pending verification.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    return render_template(
        "register.html",
        form={}
    )


# ================================================================
# Admin Creates Officer / Maintenance Staff
# ================================================================

@auth_bp.route(
    "/users/new",
    methods=["GET", "POST"]
)
@login_required
@roles_required(Role.ADMIN)
def create_staff_user():

    """
    Admin-only.

    Creates:
        - Officer
        - Maintenance Staff

    A temporary password is automatically generated.
    """

    # ------------------------------------------------------------
    # POST
    # ------------------------------------------------------------

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        role = request.form.get(
            "role",
            ""
        )

        errors = []

        # --------------------------------------------------------
        # Validate role
        # --------------------------------------------------------

        if role not in (
            Role.OFFICER,
            Role.STAFF
        ):

            errors.append(
                "Select a valid role "
                "(Officer or Maintenance Staff)."
            )

        # --------------------------------------------------------
        # Validate username
        # --------------------------------------------------------

        if not username or len(username) < 4:

            errors.append(
                "Username must be at least 4 characters."
            )

        elif not username_available(username):

            errors.append(
                "That username is already taken."
            )

        # --------------------------------------------------------
        # Show errors
        # --------------------------------------------------------

        if errors:

            for error in errors:

                flash(
                    error,
                    "danger"
                )

            return render_template(
                "users/new.html",
                form=request.form
            ), 400

        # --------------------------------------------------------
        # Generate temporary password
        # --------------------------------------------------------

        temp_password = generate_temp_password()

        # --------------------------------------------------------
        # Create Staff User
        # --------------------------------------------------------

        user = User(
            username=username,
            role=role,
            must_change_password=True
        )

        user.set_password(
            temp_password
        )

        db.session.add(user)

        db.session.commit()

        # --------------------------------------------------------
        # Show temporary password
        # --------------------------------------------------------

        flash(
            f"Account created for '{username}'. "
            f"Temporary password: {temp_password}. "
            "Share this securely with the staff member. "
            "The password must be changed after first login.",
            "success"
        )

        return redirect(
            url_for("auth.create_staff_user")
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    return render_template(
        "users/new.html",
        form={}
    )


# ================================================================
# Staff Accounts - Admin View
# ================================================================

@auth_bp.route(
    "/users",
    methods=["GET"]
)
@login_required
@roles_required(Role.ADMIN)
def list_staff_users():

    """
    Admin can view all Officer and Maintenance Staff accounts.
    """

    staff_users = User.query.filter(
        User.role.in_([
            Role.OFFICER,
            Role.STAFF
        ])
    ).all()

    return render_template(
        "users/list.html",
        staff_users=staff_users
    )


# ================================================================
# Reset Staff Password - Admin
# ================================================================

@auth_bp.route(
    "/users/<int:user_id>/reset-password",
    methods=["POST"]
)
@login_required
@roles_required(Role.ADMIN)
def reset_staff_password(user_id):

    """
    Admin resets the password of an Officer
    or Maintenance Staff.

    A new temporary password is generated.
    """

    user = db.session.get(
        User,
        user_id
    )

    if user is None:

        flash(
            "Staff account not found.",
            "danger"
        )

        return redirect(
            url_for("auth.list_staff_users")
        )

    # ------------------------------------------------------------
    # Security check
    # ------------------------------------------------------------

    if user.role not in (
        Role.OFFICER,
        Role.STAFF
    ):

        flash(
            "You can only reset Officer or "
            "Maintenance Staff passwords.",
            "danger"
        )

        return redirect(
            url_for("auth.list_staff_users")
        )

    # ------------------------------------------------------------
    # Generate temporary password
    # ------------------------------------------------------------

    temp_password = generate_temp_password()

    # ------------------------------------------------------------
    # Save new password
    # ------------------------------------------------------------

    user.set_password(
        temp_password
    )

    user.must_change_password = True

    db.session.commit()

    # ------------------------------------------------------------
    # Show temporary password
    # ------------------------------------------------------------

    flash(
        f"Password reset for '{user.username}'. "
        f"Temporary password: {temp_password}. "
        "Give this password securely to the staff member. "
        "They must change it after logging in.",
        "success"
    )

    return redirect(
        url_for("auth.list_staff_users")
    )


# ================================================================
# Delete Staff Account - Admin
# ================================================================

@auth_bp.route(
    "/users/<int:user_id>/delete",
    methods=["POST"]
)
@login_required
@roles_required(Role.ADMIN)
def delete_staff_user(user_id):

    """
    Admin can delete Officer or Maintenance Staff accounts.

    Admin accounts and Customer accounts cannot
    be deleted through this route.
    """

    user = db.session.get(
        User,
        user_id
    )

    if user is None:

        flash(
            "Staff account not found.",
            "danger"
        )

        return redirect(
            url_for("auth.list_staff_users")
        )

    # ------------------------------------------------------------
    # Security check
    # ------------------------------------------------------------

    if user.role not in (
        Role.OFFICER,
        Role.STAFF
    ):

        flash(
            "You can only delete Officer or "
            "Maintenance Staff accounts.",
            "danger"
        )

        return redirect(
            url_for("auth.list_staff_users")
        )

    # ------------------------------------------------------------
    # Save username before deleting
    # ------------------------------------------------------------

    username = user.username

    # ------------------------------------------------------------
    # Delete staff account
    # ------------------------------------------------------------

    db.session.delete(
        user
    )

    db.session.commit()

    # ------------------------------------------------------------
    # Success message
    # ------------------------------------------------------------

    flash(
        f"Staff account '{username}' has been deleted.",
        "success"
    )

    return redirect(
        url_for("auth.list_staff_users")
    )


# ================================================================
# Customer Forgot Password
# ================================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    """
    Customer password reset.

    Customer provides:
        1. Username
        2. Registered phone number

    If both match, a temporary password is generated.
    """

    # ------------------------------------------------------------
    # POST
    # ------------------------------------------------------------

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        # --------------------------------------------------------
        # Find User
        # --------------------------------------------------------

        user = User.query.filter_by(
            username=username
        ).first()

        # Only CUSTOMER can use this reset method
        if user is None or user.role != Role.CUSTOMER:

            flash(
                "Invalid username or phone number.",
                "danger"
            )

            return render_template(
                "forgot_password.html"
            ), 400

        # --------------------------------------------------------
        # Find linked Customer
        # --------------------------------------------------------

        customer = db.session.get(
            Customer,
            user.linked_customer_id
        )

        if customer is None or customer.phone != phone:

            flash(
                "Invalid username or phone number.",
                "danger"
            )

            return render_template(
                "forgot_password.html"
            ), 400

        # --------------------------------------------------------
        # Generate temporary password
        # --------------------------------------------------------

        temp_password = generate_temp_password()

        user.set_password(
            temp_password
        )

        user.must_change_password = True

        db.session.commit()

        # --------------------------------------------------------
        # Show temporary password
        # --------------------------------------------------------

        flash(
            f"Password reset successful. "
            f"Temporary password: {temp_password}. "
            "Use it to log in and change your password.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    return render_template(
        "forgot_password.html"
    )


# ================================================================
# Change Password
# ================================================================

@auth_bp.route(
    "/change-password",
    methods=["GET", "POST"]
)
@login_required
def change_password():

    # ------------------------------------------------------------
    # POST
    # ------------------------------------------------------------

    if request.method == "POST":

        current_pw = request.form.get(
            "current_password",
            ""
        )

        new_pw = request.form.get(
            "new_password",
            ""
        )

        confirm_pw = request.form.get(
            "confirm_password",
            ""
        )

        # --------------------------------------------------------
        # Check current password
        # --------------------------------------------------------

        if not current_user.check_password(
            current_pw
        ):

            flash(
                "Current password is incorrect.",
                "danger"
            )

            return render_template(
                "change_password.html"
            ), 400

        # --------------------------------------------------------
        # Password policy
        # --------------------------------------------------------

        ok, msg = password_meets_policy(
            new_pw
        )

        if not ok:

            flash(
                msg,
                "danger"
            )

            return render_template(
                "change_password.html"
            ), 400

        # --------------------------------------------------------
        # Confirm password
        # --------------------------------------------------------

        if new_pw != confirm_pw:

            flash(
                "New passwords do not match.",
                "danger"
            )

            return render_template(
                "change_password.html"
            ), 400

        # --------------------------------------------------------
        # Update password
        # --------------------------------------------------------

        current_user.set_password(
            new_pw
        )

        current_user.must_change_password = False

        db.session.commit()

        flash(
            "Password updated successfully.",
            "success"
        )

        return redirect(
            url_for("auth.dashboard")
        )

    # ------------------------------------------------------------
    # GET
    # ------------------------------------------------------------

    return render_template(
        "change_password.html"
    )


# ================================================================
# Role-Based Dashboard
# ================================================================

@auth_bp.route(
    "/dashboard",
    methods=["GET"]
)
@login_required
def dashboard():

    """
    Redirect the logged-in user to the dashboard
    appropriate for their role.

    ADMIN
        -> dashboard.html

    OFFICER
        -> officer_dashboard.html

    STAFF
        -> maintenance_dashboard.html

    CUSTOMER
        -> customer_dashboard.html
    """

    # ============================================================
    # ADMIN DASHBOARD
    # ============================================================

    if current_user.role == Role.ADMIN:

        return render_template(
            "dashboard.html"
        )

    # ============================================================
    # WATER SUPPLY OFFICER DASHBOARD
    # ============================================================

    if current_user.role == Role.OFFICER:

        return render_template(
            "officer_dashboard.html"
        )

    # ============================================================
    # MAINTENANCE STAFF DASHBOARD
    # ============================================================

    if current_user.role == Role.STAFF:

        return render_template(
            "maintenance_dashboard.html"
        )

    # ============================================================
    # CUSTOMER DASHBOARD
    # ============================================================

    if current_user.role == Role.CUSTOMER:

        return render_template(
            "customer_dashboard.html"
        )

    # ============================================================
    # UNKNOWN ROLE
    # ============================================================

    logout_user()

    flash(
        "Your account has an invalid role. "
        "Please contact the administrator.",
        "danger"
    )

    return redirect(
        url_for("auth.login")
    )