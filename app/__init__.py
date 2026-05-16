from flask import Flask
from config import Config
from app.models.database import db

def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    # Init DB
    db.init_app(app)

    # Register Blueprints
    from app.routers.main_routes import main_bp
    from app.routers.auth_routes import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    return app