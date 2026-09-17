# WSMS Premium - Water Supply Management System

Flask + SQLite water utility management system with role-based access for Admin, Water Supply Officer, Maintenance Staff and Customer.

## Features

- Customer registration and officer/admin verification
- Customer self-service password reset using **Username + registered Phone Number**
- Admin staff account management
  - Create Water Supply Officer / Maintenance Staff
  - View and edit accounts
  - Activate / deactivate accounts
  - Generate temporary passwords for resets
- Officer and Maintenance Staff temporary-password flow with forced password change
- Customer view/edit/delete management for Admin
- Safe customer deletion: deletion is blocked when billing, meter, installation, maintenance, leakage or reading-history records exist
- Meter installation and monthly reading schedules
- Bill generation and late fees
- Notification system with "Mark all as read"
- Zone management
- Responsive UI

## Setup

```text
pip install -r requirements.txt
python seed_admin.py
python app.py
```

Open `http://127.0.0.1:5000`

## Default Logins

- Admin: `admin / admin123`
- Officer: `officer / officer123`
- Staff: `staff / staff123`
- Staff2: `staff2 / staff123`
- Customer: register your own account

## Password Reset Rules

### Customer
Use **Forgot Customer Password?** on the login page. Enter the customer username and the phone number registered with that account, then create a new password.

### Officer / Maintenance Staff
These users cannot self-reset their password. They must contact an Admin. The Admin can use **Staff Accounts → Reset** to generate a temporary password. The user must use that temporary password to log in and then create a permanent password.

## Notes

- Email is optional for Admin-created staff accounts.
- Passwords are stored as secure password hashes; temporary passwords are only displayed to the Admin after a reset.
- Existing SQLite databases are upgraded automatically with the new optional `full_name` user field.
