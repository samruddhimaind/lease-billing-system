from sqlalchemy import text
from datetime import date
import io
import razorpay
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, jsonify
from flask_mail import Message
from flask_login import login_required, current_user
from app import db, mail
from app.models import Invoice, Payment, Lease
from app.services.pdf_generator import generate_invoice_pdf

bp = Blueprint('billing', __name__)

@bp.route('/invoices')
@login_required
def list_invoices():
    if current_user.role == 'admin':
        invoices = Invoice.query.order_by(Invoice.due_date.desc()).all()
    else:
        # Tenant view: sirf logged-in tenant ke records dikhana
        invoices = (
            Invoice.query
            .join(Lease)
            .filter(Lease.tenant_id == current_user.tenant_id)
            .order_by(Invoice.due_date.desc())
            .all()
        )
    return render_template('billing/invoices.html', invoices=invoices)

@bp.route('/generate-monthly-run', methods=['POST'])
@login_required
def trigger_monthly_run():
    if current_user.role != 'admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('billing.list_invoices'))

    target_date = request.form.get('target_date', date.today().strftime('%Y-%m-%d'))
    try:
        db.session.execute(text("CALL GenerateMonthlyBilling(:target_date)"), {'target_date': target_date})
        db.session.commit()
        flash(f"Monthly billing run executed successfully for {target_date}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to generate billing run: {str(e)}", "danger")

    return redirect(url_for('billing.list_invoices'))

@bp.route('/apply-late-fees', methods=['POST'])
@login_required
def trigger_late_fees():
    if current_user.role != 'admin':
        flash("Unauthorized access.", "danger")
        return redirect(url_for('billing.list_invoices'))

    target_date = request.form.get('target_date', date.today().strftime('%Y-%m-%d'))
    try:
        db.session.execute(text("CALL ApplyLateFees(:target_date)"), {'target_date': target_date})
        db.session.commit()
        flash(f"Late fees evaluated and applied successfully for {target_date}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to apply late fees: {str(e)}", "danger")

    return redirect(url_for('billing.list_invoices'))


@bp.route('/payments', methods=['POST'])
@login_required
def record_payment():
    invoice_id = request.form.get('invoice_id')
    amount_str = request.form.get('amount')
    payment_method = request.form.get('payment_method', 'bank_transfer')

    if not invoice_id or not amount_str:
        flash("Invoice ID and amount are required.", "danger")
        return redirect(url_for('billing.list_invoices'))

    try:
        payment_amount = Decimal(amount_str)
        if payment_amount <= Decimal('0.00'):
            flash("Payment amount must be greater than zero.", "danger")
            return redirect(url_for('billing.list_invoices'))

        # Enforce Row-level Locking (SELECT ... FOR UPDATE) to prevent race conditions
        invoice = db.session.query(Invoice).with_for_update().get(invoice_id)
        if not invoice:
            flash("Invoice not found.", "danger")
            return redirect(url_for('billing.list_invoices'))

        remaining_balance = invoice.amount_due - invoice.amount_paid
        if payment_amount > remaining_balance:
            flash(f"Payment exceeds remaining balance (${remaining_balance:.2f}).", "danger")
            return redirect(url_for('billing.list_invoices'))

        # Create immutable payment record
        payment = Payment(
            invoice_id=invoice.id,
            amount=payment_amount,
            payment_method=payment_method
        )
        db.session.add(payment)

        # Update invoice balance and status
        invoice.amount_paid += payment_amount
        if invoice.amount_paid >= invoice.amount_due:
            invoice.status = 'paid'
        else:
            invoice.status = 'partially_paid'

        db.session.commit()
        flash(f"Payment of ${payment_amount:.2f} recorded successfully.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Transaction failed: {str(e)}", "danger")

    return redirect(url_for('billing.list_invoices'))


@bp.route('/invoice/<int:invoice_id>/download-pdf', methods=['GET'])
@login_required
def download_invoice_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    pdf_buffer = generate_invoice_pdf(invoice)
    tenant = invoice.lease.tenant
    filename = f"Invoice_{invoice.id}_{tenant.last_name}.pdf"

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )


@bp.route('/invoice/<int:invoice_id>/email', methods=['POST'])
@login_required
def email_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    tenant = invoice.lease.tenant

    pdf_buffer = generate_invoice_pdf(invoice)
    filename = f"Invoice_{invoice.id}_{tenant.last_name}.pdf"

    msg = Message(
        subject=f"PropertyLedger Invoice #INV-{invoice.id} - Due {invoice.due_date}",
        recipients=[tenant.email],
        body=(
            f"Dear {tenant.first_name},\n\n"
            f"Please find attached your invoice for Unit {invoice.lease.unit.unit_number}.\n\n"
            f"Total Due: ${invoice.amount_due:.2f}\n"
            f"Due Date: {invoice.due_date}\n\n"
            f"Thank you,\nProperty Management Team"
        )
    )
    
    msg.attach(filename, "application/pdf", pdf_buffer.getvalue())

    try:
        mail.send(msg)
        flash(f"Invoice #INV-{invoice.id} successfully sent to {tenant.email}.", "success")
    except Exception as e:
        flash(f"Failed to send email: {str(e)}", "danger")

    return redirect(url_for('billing.list_invoices'))


@bp.route('/invoice/<int:invoice_id>/pay-online', methods=['POST'])
@login_required
def create_payment_order(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    remaining_balance = float(invoice.amount_due - invoice.amount_paid)

    if remaining_balance <= 0:
        return jsonify({'error': 'Invoice already paid'}), 400

    client = razorpay.Client(auth=(
        current_app.config['RAZORPAY_KEY_ID'], 
        current_app.config['RAZORPAY_KEY_SECRET']
    ))

    # Razorpay expects amounts in paise (1 INR = 100 paise)
    order_data = {
        'amount': int(remaining_balance * 100),
        'currency': 'INR',
        'receipt': f'inv_rcpt_{invoice.id}',
        'notes': {
            'invoice_id': invoice.id,
            'tenant_id': invoice.lease.tenant_id
        }
    }
    
    try:
        order = client.order.create(data=order_data)
        return jsonify({
            'order_id': order['id'],
            'amount': order['amount'],
            'key_id': current_app.config['RAZORPAY_KEY_ID'],
            'currency': 'INR'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500