from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from app.config import Config

db = SQLAlchemy()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    mail.init_app(app)

    from app.routes.billing import bp as billing_bp
    from app.routes.reports import bp as reports_bp

    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(reports_bp, url_prefix='/reports')

    # Root route must be inside create_app
    @app.route('/')
    def index():
        return redirect(url_for('billing.list_invoices'))

    return app