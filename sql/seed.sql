USE real_estate_db;

-- Clear previous test data (respecting foreign key order)
DELETE FROM payments;
DELETE FROM invoices;
DELETE FROM leases;
DELETE FROM tenants;
DELETE FROM units;

-- 1. Insert Units
INSERT INTO units (id, unit_number, floor_plan, base_rent, status) VALUES
(1, '101', '1BHK - Studio', 1200.00, 'occupied'),
(2, '102', '2BHK - Deluxe', 1800.00, 'occupied'),
(3, '201', '2BHK - Deluxe', 1850.00, 'vacant'),
(4, '202', '3BHK - Penthouse', 2500.00, 'maintenance');

-- 2. Insert Tenants
INSERT INTO tenants (id, first_name, last_name, email, phone) VALUES
(1, 'Aarav', 'Sharma', 'aarav.sharma@example.com', '9876543210'),
(2, 'Priya', 'Patel', 'priya.patel@example.com', '9823456780');

-- 3. Insert Leases
-- Lease 1: Mid-month move-in on September 16, 2026 (September has 30 days -> 15 billable days)
-- Proration formula: (1200 / 30) * 15 = 600.00
INSERT INTO leases (id, unit_id, tenant_id, start_date, end_date, monthly_rent, security_deposit, status) VALUES
(1, 1, 1, '2026-09-16', '2027-09-15', 1200.00, 1200.00, 'active');

-- Lease 2: Standard lease started earlier (full month rent = 1800.00)
INSERT INTO leases (id, unit_id, tenant_id, start_date, end_date, monthly_rent, security_deposit, status) VALUES
(2, 2, 2, '2026-01-01', '2026-12-31', 1800.00, 1800.00, 'active');