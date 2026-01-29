# Accounting Manager Skill

## Description
Manages Odoo accounting integration for invoices, expenses, contacts, and financial reporting.

## Triggers
- Invoice creation request
- Expense submission
- Financial report generation
- Overdue invoice alerts

## Capabilities
1. **Invoice Management**: Create, post, and track invoices
2. **Expense Tracking**: Log and categorize business expenses
3. **Contact Management**: Manage customers and vendors
4. **Financial Reports**: Generate summaries and aging reports
5. **Payment Tracking**: Monitor outstanding balances

## Commands

### Test Odoo Connection
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
source venv/bin/activate
python watchers/odoo_integration.py --test
```

### Get Financial Summary
```bash
python watchers/odoo_integration.py --summary
```

### Generate Aging Report
```bash
python watchers/odoo_integration.py --aging
```

### List Overdue Invoices
```bash
python watchers/odoo_integration.py --overdue
```

## Environment Variables
Add to `.env` file:
```
ODOO_URL=https://your-company.odoo.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-email@example.com
ODOO_API_KEY=your-api-key
```

## Approval Workflow
1. User requests invoice/expense creation
2. AI Employee creates approval request in `Approvals/`
3. Human reviews and approves
4. Approval Executor creates record in Odoo
5. Confirmation logged and moved to `Done/`

## Invoice Approval Format
```markdown
---
type: invoice_approval
partner: Customer Name
amount: 1000.00
status: pending
---

# Invoice Approval Request

## Details
- Customer: ABC Company
- Amount: $1,000.00
- Description: Consulting services

## Action Required
Move to Approved/ folder to create invoice in Odoo.
```

## Safety Rules
1. All financial actions require human approval
2. Never auto-approve invoices over $100
3. Log all Odoo operations
4. Validate data before submission
5. Require confirmation for deletions
