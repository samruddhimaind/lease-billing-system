from flask import send_file
from app.services.pdf_generator import generate_invoice_pdf
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Invoice, Payment
from sqlalchemy import text
from datetime import datetime
import uuid

bp = Blueprint('billing', __name__)

@bp.route('/invoices')
def list_invoices():
    # Fetch all invoices sorted by most recent
    invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).all()
    return render_template('billing/invoices.html', invoices=invoices)

@bp.route('/run-monthly', methods=['POST'])
def trigger_monthly_run():
    month = int(request.form.get('month', datetime.now().month))
    year = int(request.form.get('year', datetime.now().year))

    try:
        # Call MySQL stored procedure
        db.session.execute(
            text("CALL GenerateMonthlyBilling(:month, :year)"),
            {'month': month, 'year': year}
        )
        db.session.commit()
        flash(f"Monthly billing run executed successfully for {month}/{year}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Billing procedure error: {str(e)}", "danger")

    return redirect(url_for('billing.list_invoices'))

@bp.route('/apply-late-fees', methods=['POST'])
def trigger_late_fees():
    cutoff = request.form.get('cutoff_date', datetime.now().strftime('%Y-%m-%d'))
    try:
        db.session.execute(
            text("CALL ApplyLateFees(:cutoff)"),
            {'cutoff': cutoff}
        )
        db.session.commit()
        flash(f"Late fees assessed successfully for cutoff date {cutoff}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Late fee calculation error: {str(e)}", "danger")

    return redirect(url_for('billing.list_invoices'))

@bp.route('/pay/<int:invoice_id>', methods=['POST'])
def record_payment(invoice_id):
    # Lock the invoice row for update to prevent concurrent double-crediting
    invoice = Invoice.query.with_for_update().get_or_404(invoice_id)
    payment_amount = float(request.form.get('amount', 0))
    method = request.form.get('method')
    ref = request.form.get('reference_no') or f"PAY-{uuid.uuid4().hex[:8].upper()}"

    if payment_amount <= 0:
        flash("Payment amount must be greater than zero.", "warning")
        return redirect(url_for('billing.list_invoices'))

    remaining_balance = float(invoice.amount_due) - float(invoice.amount_paid)
    if payment_amount > remaining_balance:
        flash(f"Payment exceeds remaining balance. Max allowed: ${remaining_balance:.2f}", "warning")
        return redirect(url_for('billing.list_invoices'))

    try:
        # Ledger entry
        payment = Payment(
            invoice_id=invoice.id,
            amount=payment_amount,
            payment_method=method,
            reference_no=ref
        )

        # Update invoice balance and status
        invoice.amount_paid = float(invoice.amount_paid) + payment_amount
        if invoice.amount_paid >= invoice.amount_due:
            invoice.status = 'paid'
        else:
            invoice.status = 'partially_paid'

        db.session.add(payment)
        db.session.commit()
        flash(f"Payment of ${payment_amount:.2f} processed (Ref: {ref}).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Transaction failed: {str(e)}", "danger")

    return redirect(url_for('billing.list_invoices'))
@bp.route('/invoice/<int:invoice_id>/download-pdf', methods=['GET'])
def download_invoice_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    pdf_buffer = generate_invoice_pdf(invoice)

    filename = f"Invoice_{invoice.id}_{invoice.lease.tenant.last_name}.pdf"
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )