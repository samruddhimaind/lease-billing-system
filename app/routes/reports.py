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