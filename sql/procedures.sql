USE real_estate_db;

DELIMITER //

-- Procedure 1: Generate Monthly Rent & Mid-Month Proration
DROP PROCEDURE IF EXISTS GenerateMonthlyBilling//

CREATE PROCEDURE GenerateMonthlyBilling(
    IN target_month INT,
    IN target_year INT
)
proc_main: BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_lease_id INT;
    DECLARE v_start_date DATE;
    DECLARE v_end_date DATE;
    DECLARE v_monthly_rent DECIMAL(10, 2);
    DECLARE v_days_in_month INT;
    DECLARE v_billable_days INT;
    DECLARE v_final_charge DECIMAL(10, 2);
    DECLARE v_charge_type VARCHAR(20);
    DECLARE v_cycle_start DATE;
    DECLARE v_cycle_end DATE;

    -- Cursor across active leases valid during the target month
    DECLARE lease_cursor CURSOR FOR
        SELECT id, start_date, end_date, monthly_rent
        FROM leases
        WHERE status = 'active'
          AND start_date <= v_cycle_end
          AND end_date >= v_cycle_start;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    -- Roll back entire transaction if any SQL error occurs
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET v_cycle_start = STR_TO_DATE(CONCAT(target_year, '-', LPAD(target_month, 2, '00'), '-01'), '%Y-%m-%d');
    SET v_cycle_end = LAST_DAY(v_cycle_start);
    SET v_days_in_month = DAY(v_cycle_end);

    START TRANSACTION;

    OPEN lease_cursor;

    read_loop: LOOP
        FETCH lease_cursor INTO v_lease_id, v_start_date, v_end_date, v_monthly_rent;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Prevent duplicate billing for the same month/year
        IF NOT EXISTS (
            SELECT 1 FROM invoices 
            WHERE lease_id = v_lease_id 
              AND MONTH(invoice_date) = target_month 
              AND YEAR(invoice_date) = target_year 
              AND charge_type IN ('rent', 'prorated_rent')
        ) THEN
            -- Check for mid-month move-in
            IF YEAR(v_start_date) = target_year AND MONTH(v_start_date) = target_month THEN
                SET v_billable_days = v_days_in_month - DAY(v_start_date) + 1;
                SET v_final_charge = ROUND((v_monthly_rent / v_days_in_month) * v_billable_days, 2);
                SET v_charge_type = 'prorated_rent';
            ELSE
                SET v_final_charge = v_monthly_rent;
                SET v_charge_type = 'rent';
            END IF;

            INSERT INTO invoices (
                lease_id, 
                invoice_date, 
                due_date, 
                amount_due, 
                amount_paid, 
                charge_type, 
                status
            )
            VALUES (
                v_lease_id,
                v_cycle_start,
                DATE_ADD(v_cycle_start, INTERVAL 4 DAY),
                v_final_charge,
                0.00,
                v_charge_type,
                'pending'
            );
        END IF;
    END LOOP;

    CLOSE lease_cursor;
    COMMIT;
END proc_main //

-- Procedure 2: Assess Late Fees on Overdue Invoices
DROP PROCEDURE IF EXISTS ApplyLateFees//

CREATE PROCEDURE ApplyLateFees(IN cutoff_date DATE)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_invoice_id INT;
    DECLARE v_lease_id INT;
    
    DECLARE overdue_cursor CURSOR FOR
        SELECT id, lease_id
        FROM invoices
        WHERE due_date < cutoff_date
          AND status IN ('pending', 'partially_paid')
          AND charge_type IN ('rent', 'prorated_rent');

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    START TRANSACTION;

    OPEN overdue_cursor;

    fee_loop: LOOP
        FETCH overdue_cursor INTO v_invoice_id, v_lease_id;
        IF done THEN
            LEAVE fee_loop;
        END IF;

        -- Mark the overdue invoice
        UPDATE invoices SET status = 'overdue' WHERE id = v_invoice_id;

        -- Add late fee if not already applied for this cycle
        IF NOT EXISTS (
            SELECT 1 FROM invoices 
            WHERE lease_id = v_lease_id 
              AND charge_type = 'late_fee' 
              AND invoice_date = cutoff_date
        ) THEN
            INSERT INTO invoices (
                lease_id, 
                invoice_date, 
                due_date, 
                amount_due, 
                amount_paid, 
                charge_type, 
                status
            )
            VALUES (
                v_lease_id, 
                cutoff_date, 
                DATE_ADD(cutoff_date, INTERVAL 3 DAY), 
                50.00, 
                0.00, 
                'late_fee', 
                'pending'
            );
        END IF;
    END LOOP;

    CLOSE overdue_cursor;
    COMMIT;
END //

DELIMITER ;