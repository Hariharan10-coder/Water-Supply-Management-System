from app import create_app
from extensions import db
from models import User, Role

app = create_app()

with app.app_context():
    if not User.query.filter_by(username="admin").first():
        admin = User(full_name="System Administrator", username="admin", role=Role.ADMIN, email="admin@wsms.com", phone="9000000001")
        admin.set_password("admin123")
        db.session.add(admin)

        officer = User(full_name="Water Supply Officer", username="officer", role=Role.OFFICER, email="officer@wsms.com", phone="9000000002")
        officer.set_password("officer123")
        db.session.add(officer)

        staff = User(full_name="Maintenance Staff", username="staff", role=Role.STAFF, email="staff@wsms.com", phone="9000000003")
        staff.set_password("staff123")
        db.session.add(staff)

        staff2 = User(full_name="Maintenance Staff 2", username="staff2", role=Role.STAFF, email="staff2@wsms.com", phone="9000000004")
        staff2.set_password("staff123")
        db.session.add(staff2)

        db.session.commit()
        print("=" * 50)
        print("Default users created:")
        print("Admin:    admin / admin123")
        print("Officer:  officer / officer123")
        print("Staff:    staff / staff123")
        print("Staff2:   staff2 / staff123")
        print("=" * 50)
    else:
        print("Users already exist.")
