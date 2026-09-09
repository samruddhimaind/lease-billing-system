\# Real Estate Lease \& Tenant Billing Management System



A robust property management and automated lease billing backend built with **Python, Flask, MySQL, and Bootstrap 5**. The system enforces strict financial double-entry tracking, database-level proration procedures, and transactional integrity.



\#  Key Architectural Features



\- **Normalized Relational Schema (3NF):** Designed with explicit foreign keys, check constraints, and indexed lookups across `units`, `tenants`, `leases`, `invoices`, and `payments`.

\- **Database-Level Stored Procedures:**

&#x20; - GenerateMonthlyBilling: Handles mid-month move-in proration calculations using dynamic calendar month boundary math directly in MySQL.

&#x20; - ApplyLateFees: Evaluates overdue balances against billing cutoff dates and appends penalties automatically.

\- **Transactional Ledger Integrity:** Leverages atomic database transactions (`with\_for\_update()`) to prevent race conditions and enforce ledger reconciliation.

\- **Live Reporting \& Analytics:** Aggregates real-time occupancy percentages and calculates accounts receivable reconciliation metrics.

\- **Automated Verification:**Comprehensive test suite built with `pytest` covering month boundary conditions, proration math, and status transition states.



\---



\# Database Schema Overview



\- **units**: Manages real estate unit numbers, floor plans, baseline rent, and availability (`vacant`, `occupied`, `maintenance`).

\- **tenants**: Client master records with unique email constraints.

\- **leases**: Binds units to tenants with fixed dates, deposits, and active lease statuses.

\- **invoices**: Tracks itemized charges (`rent`, `prorated\_rent`, `late\_fee`, `deposit`), due dates, and settlement states.

\-**payments**: Append-only transactional payment ledger with unique transaction references.



\---



\# Getting Started



&#x20;1. Prerequisites

\- Python 3.10+

\- MySQL Server 8.0+



2\. Local Setup



1\. **Clone the repository:**

&#x20;  ```bash

&#x20;  git clone \[https://github.com/your-username/lease-billing-system.git](https://github.com/your-username/lease-billing-system.git)

&#x20;  cd lease-billing-system

