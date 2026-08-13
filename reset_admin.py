from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():

    admin = db.session.execute(
        db.select(User).filter_by(username="admin")
    ).scalar_one_or_none()

    if admin:
        admin.password_hash = generate_password_hash("Admin@1234")
        db.session.commit()

        print("================================")
        print("Admin password changed successfully")
        print("Username: admin")
        print("Password: Admin@1234")
        print("================================")

    else:
        print("Admin user not found.")

