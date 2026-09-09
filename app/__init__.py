from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        # Import and register blueprints
        from app.routes.billing import bp as billing_bp
        from app.routes.reports import bp as reports_bp

        app.register_blueprint(billing_bp, url_prefix='/billing')
        app.register_blueprint(reports_bp, url_prefix='/reports')

    return app