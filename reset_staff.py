from app import create_app
from extensions import db
from models import User
from utils.auth_utils import generate_temp_password

app = create_app()

with app.app_context():

    username = input("Enter staff username: ").strip()

    user = User.query.filter_by(username=username).first()

    if not user:
        print("User not found.")
    elif user.role not in ("officer", "staff"):
        print("This user is not an Officer or Maintenance Staff.")
    else:
        temp_password = generate_temp_password()

        user.set_password(temp_password)
        user.must_change_password = True

        db.session.commit()

        print()
        print("===================================")
        print("Password reset successfully")
        print("Username:", user.username)
        print("Temporary password:", temp_password)
        print("===================================")