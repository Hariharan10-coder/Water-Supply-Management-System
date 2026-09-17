import os
from flask import Flask
from config import Config
from extensions import db, login_manager, csrf
from models import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes.auth_routes import auth_bp
    from routes.customer_routes import customer_bp
    from routes.meter_routes import meter_bp
    from routes.billing_routes import billing_bp
    from routes.maintenance_routes import maintenance_bp
    from routes.leakage_routes import leakage_bp
    from routes.installation_routes import installation_bp
    from routes.notification_routes import notification_bp
    from routes.user_routes import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(meter_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(leakage_bp)
    app.register_blueprint(installation_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(user_bp)

    # Context processor for notification count
    @app.context_processor
    def inject_notifications():
        from flask_login import current_user
        from services.notification_service import NotificationService
        if current_user.is_authenticated:
            count = NotificationService.get_unread_count(current_user.user_id)
            return {"unread_count": count}
        return {"unread_count": 0}

    with app.app_context():
        db.create_all()

        # create_all() does not add columns to an existing SQLite table.
        # Add the new optional full_name field when upgrading an old database.
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if "users" in inspector.get_table_names():
            user_columns = {col["name"] for col in inspector.get_columns("users")}
            if "full_name" not in user_columns:
                with db.engine.begin() as conn:
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN full_name VARCHAR(100)"
                    ))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
