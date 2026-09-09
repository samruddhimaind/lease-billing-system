import pytest
from datetime import date
import calendar

def calculate_proration(monthly_rent: float, start_date: date) -> float:
    """
    Python mirror of the MySQL stored procedure's mathematical logic:
    Prorated Charge = (Monthly Rent / Days in Month) * Billable Days
    """
    days_in_month = calendar.monthrange(start_date.year, start_date.month)[1]
    billable_days = days_in_month - start_date.day + 1
    return round((monthly_rent / days_in_month) * billable_days, 2)


# --- Unit Tests: Proration Math ---

def test_proration_mid_month_30_days():
    """Test mid-month lease start in a 30-day month (e.g., September 16)."""
    monthly_rent = 1200.00
    start = date(2026, 9, 16)  # 15 billable days (16th to 30th inclusive)
    expected = round((1200.00 / 30) * 15, 2)  # Exactly 600.00
    assert calculate_proration(monthly_rent, start) == expected


def test_proration_mid_month_31_days():
    """Test mid-month lease start in a 31-day month (e.g., October 15)."""
    monthly_rent = 1550.00
    start = date(2026, 10, 15)  # 17 billable days
    expected = round((1550.00 / 31) * 17, 2)  # Exactly 850.00
    assert calculate_proration(monthly_rent, start) == expected


def test_proration_first_day_of_month():
    """Starting on the 1st day should result in 100% full monthly rent."""
    monthly_rent = 2000.00
    start = date(2026, 9, 1)
    assert calculate_proration(monthly_rent, start) == monthly_rent


def test_proration_last_day_of_month():
    """Starting on the last day of the month should bill exactly 1 day."""
    monthly_rent = 3000.00
    start = date(2026, 9, 30)  # 1 billable day
    expected = round((3000.00 / 30) * 1, 2)  # 100.00
    assert calculate_proration(monthly_rent, start) == expected


# --- Unit Tests: Payment & Ledger Balance Logic ---

def test_payment_status_transitions():
    """Verify state transitions: pending -> partially_paid -> paid."""
    amount_due = 1000.00
    amount_paid = 0.00
    status = "pending"

    # Transaction 1: Partial payment of $400
    payment_1 = 400.00
    amount_paid += payment_1
    status = "paid" if amount_paid >= amount_due else "partially_paid"
    
    assert amount_paid == 400.00
    assert status == "partially_paid"

    # Transaction 2: Remaining payment of $600
    payment_2 = 600.00
    amount_paid += payment_2
    status = "paid" if amount_paid >= amount_due else "partially_paid"

    assert amount_paid == 1000.00
    assert status == "paid"


def test_overpayment_guard():
    """Ensure excess payment is flagged as invalid."""
    amount_due = 500.00
    amount_paid = 200.00
    remaining_due = amount_due - amount_paid

    incoming_payment = 350.00
    is_valid = incoming_payment <= remaining_due
    assert is_valid is False