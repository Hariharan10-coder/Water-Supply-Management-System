# Water Supply Management System

A web-based Water Supply Management System developed using **Python, Flask, SQLite, HTML, CSS, and Jinja2**.

The system manages water supply operations through role-based access for:

- Admin
- Water Supply Officer
- Maintenance Staff
- Customer

---

## Features

### Authentication

- User login
- User logout
- Customer registration
- Password hashing
- Password policy validation
- Forgot password
- Change password
- Temporary password generation
- Role-based access control

### Role-Based Dashboards

Different users are redirected to their appropriate dashboard after login.

| Role | Dashboard |
|---|---|
| Admin | `dashboard.html` |
| Officer | `officer_dashboard.html` |
| Maintenance Staff | `maintenance_dashboard.html` |
| Customer | `customer_dashboard.html` |

### Admin

The Admin can:

- View the Admin dashboard
- Create Officer accounts
- Create Maintenance Staff accounts
- View staff accounts
- Reset staff passwords
- Delete staff accounts
- Manage customers

### Officer

The Officer dashboard is designed for water supply administration and service management.

### Maintenance Staff

The Maintenance Staff dashboard is designed for:

- Viewing assigned maintenance work
- Tracking maintenance status
- Updating work progress
- Viewing completed maintenance work

### Customer

The Customer dashboard is designed for customers to access their water supply services and account information.

---

## Technologies Used

- **Python**
- **Flask**
- **SQLite**
- **Flask-SQLAlchemy**
- **Flask-Login**
- **HTML5**
- **CSS3**
- **Jinja2**

---

## Project Structure

```text
wsms_app/
│
├── app.py
├── config.py
├── extensions.py
├── requirements.txt
│
├── models/
│   ├── __init__.py
│   ├── customer_model.py
│   └── user_model.py
│
├── routes/
│   ├── __init__.py
│   ├── auth_routes.py
│   └── customer_routes.py
│
├── services/
│   ├── __init__.py
│   └── rbac_service.py
│
├── utils/
│   ├── __init__.py
│   ├── auth_utils.py
│   └── validators.py
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── forgot_password.html
│   ├── change_password.html
│   ├── dashboard.html
│   ├── officer_dashboard.html
│   ├── maintenance_dashboard.html
│   ├── customer_dashboard.html
│   │
│   ├── customers/
│   │   ├── form.html
│   │   └── list.html
│   │
│   └── users/
│       ├── new.html
│       └── list.html
│
├── static/
│   └── css/
│       └── style.css
│
├── seed_admin.py
├── reset_admin.py
├── reset_staff.py
│
└── .gitignore