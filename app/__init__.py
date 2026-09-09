from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from sqlalchemy import text
from app.config import Config

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
scheduler = APScheduler()

def auto_monthly_billing(app):
    with app.app_context():
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        db.session.execute(text("CALL GenerateMonthlyBilling(:target_date)"), {'target_date': today})
        db.session.commit()
        print(f"[Scheduler] Generated automated monthly billing for {today}")

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    # Initialize and start Scheduler
    app.config['SCHEDULER_API_ENABLED'] = False
    scheduler.init_app(app)
    scheduler.start()

    if not scheduler.get_job('monthly_billing_job'):
        scheduler.add_job(
            id='monthly_billing_job',
            func=auto_monthly_billing,
            args=[app],
            trigger='cron',
            day='1',
            hour='0',
            minute='1'
        )

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.auth import bp as auth_bp
    from app.routes.billing import bp as billing_bp
    from app.routes.reports import bp as reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(reports_bp, url_prefix='/reports')

    @app.route('/')
    def index():
        return redirect(url_for('billing.list_invoices'))

    return app