\# Real Estate Lease \& Tenant Billing Management System



A production-grade property management and billing ledger built with Flask, SQLAlchemy, MySQL 8.0, and Bootstrap 5. The platform offloads critical financial business logic to MySQL stored procedures, guarantees ledger consistency with row-level transaction locks (`with\_for\_update`), and automates document synthesis and delivery via ReportLab and Flask-Mail.







\# Key Features



\- **Automated Billing Stored Procedure (`GenerateMonthlyBilling`)**: Generates monthly rental charges while automatically computing calendar-day proration for mid-month move-ins ($(\\text{Monthly Rent} / \\text{Days in Month}) \\times \\text{Days Occupied}$) directly in MySQL.

\- **Late Fee Automation (ApplyLateFees)**: Evaluates overdue invoices past grace periods in batch and generates penalty invoices automatically.

\- **Race Condition Prevention:** Enforces database row locking (`SELECT ... FOR UPDATE`) during payment allocations to prevent double-crediting or balance inconsistencies under concurrent access.

\- **Automated In-Memory PDF Generation**: Synthesizes branded vector PDF invoices in-memory via ReportLab without disk I/O bottlenecks.

\- **SMTP Email Dispatch:** Automatically dispatches invoice notifications and attaches the generated PDF invoice directly to the tenant's email address using Flask-Mail.

\- **Lease Expiration \& Notice Tracker:** Proactively tracks leases terminating within 30, 60, and 120-day windows with color-coded urgency badges to streamline renewal notices.

\- **Financial Audit Trails:** Normalized 3NF relational schema configured with `ON DELETE RESTRICT` to prevent accidental cascades or purging of invoice and payment ledgers.







\#Tech Stack



\- **Backend:** Python 3.11, Flask (Application Factory \& Blueprints Pattern), Flask-SQLAlchemy

\- **Database:** MySQL 8.0 (InnoDB, Stored Procedures, ACID Transactions)

\- **Document Generation:** ReportLab 4.1.0

\- **Email Service:** Flask-Mail 0.10.0 (SMTP / Sandbox Testing via Mailtrap)

\- **Frontend:** Bootstrap 5, Bootstrap Icons, Jinja2 Templates

\- **Testing:** pytest







\# Database Architecture (3NF)



The schema enforces data normalization and strict audit boundaries across 5 core entities:



1\. units: Physical property spaces, floor plans, and occupancy flags.

2\. tenants: Contact details and tenant metadata.

3\. leases: Binding agreements mapping tenants to units, rental amounts, and term dates.

4\. invoices: Billable line items, charge types, total due, balance settled, and status (pending, partially\_paid, paid).

5\. payments: Immutable payment transaction records linked directly to invoice records.







\# Project Structure



```text

lease\_billing\_system/

├── app/

│   ├── routes/

│   │   ├── billing.py          # Invoice, payment, PDF \& email routes

│   │   └── reports.py          # Occupancy \& lease expiration routes

│   ├── services/

│   │   └── pdf\_generator.py    # ReportLab PDF synthesis service

│   ├── templates/

│   │   ├── base.html

│   │   ├── billing/

│   │   │   └── invoices.html

│   │   └── reports/

│   │       └── expirations.html

│   ├── \_\_init\_\_.py             # Flask app factory \& extension init

│   ├── config.py               # Environment configuration loader

│   └── models.py               # SQLAlchemy 3NF models

├── sql/

│   ├── schema.sql              # Table definitions \& foreign keys

│   └── procedures.sql          # Stored procedures for billing \& late fees

├── tests/

│   └── test\_billing.py         # Pytest test cases

├── .env.example

├── .gitignore

├── README.md

├── requirements.txt

└── run.py                      # Application entry point

