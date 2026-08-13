import os
from flask import Flask

from config import DevelopmentConfig, ProductionConfig
from extensions import db, login_manager, csrf
from models import User


def create_app():
    app = Flask(__name__)

    env = os.environ.get("FLASK_ENV", "development")
    app.config.from_object(ProductionConfig if env == "production" else DevelopmentConfig)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from routes.auth_routes import auth_bp
    from routes.customer_routes import customer_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
