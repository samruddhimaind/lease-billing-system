from datetime import date, timedelta
from flask import Blueprint, render_template
from app.models import Lease
from flask import Blueprint, render_template
from app import db
from sqlalchemy import text

bp = Blueprint('reports', __name__)

@bp.route('/occupancy')
def occupancy_summary():
    # Direct aggregation query to calculate live occupancy rates
    query = text("""
        SELECT 
            COUNT(*) AS total_units,
            SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) AS occupied_units,
            SUM(CASE WHEN status = 'vacant' THEN 1 ELSE 0 END) AS vacant_units,
            ROUND((SUM(CASE WHEN status = 'occupied' THEN 1 ELSE 0 END) / COUNT(*)) * 100, 2) AS occupancy_rate
        FROM units
    """)
    result = db.session.execute(query).mappings().first()
    return render_template('reports/occupancy.html', data=result)

@bp.route('/reconciliation')
def financial_reconciliation():
    # Aggregation for financial reconciliation by charge type
    query = text("""
        SELECT 
            charge_type,
            COUNT(*) AS invoice_count,
            SUM(amount_due) AS total_billed,
            SUM(amount_paid) AS total_collected,
            (SUM(amount_due) - SUM(amount_paid)) AS total_outstanding
        FROM invoices
        GROUP BY charge_type
    """)
    records = db.session.execute(query).mappings().all()
    return render_template('reports/reconciliation.html', records=records)
@bp.route('/expirations', methods=['GET'])
def lease_expirations():
    today = date.today()
    in_90_days = today + timedelta(days=90)

    # Query active leases expiring within the next 90 days
    expiring_leases = (
        Lease.query
        .filter(Lease.status == 'active')
        .filter(Lease.end_date >= today)
        .filter(Lease.end_date <= in_90_days)
        .order_by(Lease.end_date.asc())
        .all()
    )

    # Calculate remaining days and categorize urgency levels
    report_data = []
    for lease in expiring_leases:
        days_left = (lease.end_date - today).days
        report_data.append({
            'lease': lease,
            'days_left': days_left,
            'urgency': 'danger' if days_left <= 30 else ('warning' if days_left <= 60 else 'info')
        })

    return render_template('reports/expirations.html', records=report_data, today=today)