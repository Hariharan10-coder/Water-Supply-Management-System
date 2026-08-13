"""
Creates the first Admin account. This is intentionally NOT a web route —
per SRS §8, there is no code path that lets anyone reach Admin except
another Admin, or this one-time CLI seed at deployment.

Usage:
    python seed_admin.py
"""
import getpass
from app import create_app
from extensions import db
from models import User, Role
from utils.auth_utils import password_meets_policy

app = create_app()

with app.app_context():
    if User.query.filter_by(role=Role.ADMIN).first():
        print("An Admin account already exists. Aborting.")
        raise SystemExit(0)

    username = input("Admin username: ").strip()
    password = getpass.getpass("Admin password: ")

    ok, msg = password_meets_policy(password)
    if not ok:
        print(f"Rejected: {msg}")
        raise SystemExit(1)

    admin = User(username=username, role=Role.ADMIN)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    print(f"Admin account '{username}' created.")
