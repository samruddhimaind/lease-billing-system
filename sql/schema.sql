-- Create database if it does not exist
CREATE DATABASE IF NOT EXISTS real_estate_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE real_estate_db;

-- Drop tables in reverse order of dependencies if re-running
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS leases;
DROP TABLE IF EXISTS tenants;
DROP TABLE IF EXISTS units;

-- 1. Units Table: property inventory
CREATE TABLE units (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unit_number VARCHAR(20) NOT NULL UNIQUE,
    floor_plan VARCHAR(50) NOT NULL,
    base_rent DECIMAL(10, 2) NOT NULL CHECK (base_rent >= 0),
    status ENUM('vacant', 'occupied', 'maintenance') DEFAULT 'vacant',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Tenants Table: tenant master records
CREATE TABLE tenants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_tenant_email (email)
) ENGINE=InnoDB;

-- 3. Leases Table: contractual links between tenant and unit
CREATE TABLE leases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    unit_id INT NOT NULL,
    tenant_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    monthly_rent DECIMAL(10, 2) NOT NULL CHECK (monthly_rent > 0),
    security_deposit DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status ENUM('active', 'terminated', 'expired') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_lease_dates (start_date, end_date)
) ENGINE=InnoDB;

-- 4. Invoices Table: monthly bills, prorated rent, and charges
CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lease_id INT NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    amount_due DECIMAL(10, 2) NOT NULL CHECK (amount_due >= 0),
    amount_paid DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (amount_paid >= 0),
    charge_type ENUM('rent', 'prorated_rent', 'late_fee', 'utility', 'deposit') NOT NULL,
    status ENUM('pending', 'paid', 'partially_paid', 'overdue') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lease_id) REFERENCES leases(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_invoice_status (status),
    INDEX idx_invoice_cycle (invoice_date, due_date)
) ENGINE=InnoDB;

-- 5. Payments Table: financial transaction ledger
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    payment_method ENUM('card', 'ach', 'bank_transfer', 'cash', 'check') NOT NULL,
    reference_no VARCHAR(100) NOT NULL UNIQUE,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_payment_date (payment_date)
) ENGINE=InnoDB;