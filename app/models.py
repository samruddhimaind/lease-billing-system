from app import db
from datetime import datetime

class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    unit_number = db.Column(db.String(20), unique=True, nullable=False)
    floor_plan = db.Column(db.String(50), nullable=False)
    base_rent = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('vacant', 'occupied', 'maintenance'), default='vacant')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    leases = db.relationship('Lease', backref='unit', lazy=True)


class Tenant(db.Model):
    __tablename__ = 'tenants'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    leases = db.relationship('Lease', backref='tenant', lazy=True)


class Lease(db.Model):
    __tablename__ = 'leases'

    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    monthly_rent = db.Column(db.Numeric(10, 2), nullable=False)
    security_deposit = db.Column(db.Numeric(10, 2), default=0.00)
    status = db.Column(db.Enum('active', 'terminated', 'expired'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    invoices = db.relationship('Invoice', backref='lease', lazy=True)


class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('leases.id'), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    amount_due = db.Column(db.Numeric(10, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), default=0.00)
    charge_type = db.Column(
        db.Enum('rent', 'prorated_rent', 'late_fee', 'utility', 'deposit'),
        nullable=False
    )
    status = db.Column(
        db.Enum('pending', 'paid', 'partially_paid', 'overdue'),
        default='pending'
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    payments = db.relationship('Payment', backref='invoice', lazy=True)


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(
        db.Enum('card', 'ach', 'bank_transfer', 'cash', 'check'),
        nullable=False
    )
    reference_no = db.Column(db.String(100), unique=True, nullable=False)