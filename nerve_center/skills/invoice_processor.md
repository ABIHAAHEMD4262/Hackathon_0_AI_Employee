# Skill: Invoice Processor

## Description
Extract data from invoices, track payments, and manage financial records.

## Trigger
- File with "invoice" in name detected
- PDF/image detected with invoice patterns
- Email with invoice attachment

## Inputs
- `file_path`: Path to invoice file
- `source`: Where invoice came from (email, upload, etc.)

## Process

### Step 1: Extract Invoice Data
```
Required fields:
- Vendor/Company name
- Invoice number
- Invoice date
- Due date
- Line items (description, quantity, unit price, total)
- Subtotal
- Tax (if applicable)
- Total amount
- Payment instructions
```

### Step 2: Validate Data
```
Check for:
- Valid date formats
- Amounts add up correctly
- Currency is expected (USD, EUR, etc.)
- Vendor exists in contacts or is new
```

### Step 3: Check Against Expected
```
Compare with:
- Recurring subscriptions list
- Outstanding quotes/proposals
- Expected project expenses
```

### Step 4: Categorize Expense
```
Categories:
- Software/Subscriptions
- Contractor/Freelancer
- Office/Supplies
- Marketing/Advertising
- Professional Services
- Utilities
- Other
```

### Step 5: Determine Approval
```
Based on Company_Handbook.md thresholds:
- Amount <= $50: Log only
- Amount $50-$100: Log + Notify
- Amount > $100: Require explicit approval
- Amount > $500: Require approval + review
- Unexpected vendor: Always require approval
```

### Step 6: Create Record
```
Save to nerve_center/finances/invoices/:
- Original file
- Extracted JSON data
- Processing notes
```

### Step 7: Update Dashboard
```
Add to financial section:
- Invoice received notification
- Update payables total
- Add due date to calendar
```

## Output
```json
{
  "invoice_id": "INV-2026-001",
  "vendor": "Example Corp",
  "amount": 149.99,
  "currency": "USD",
  "due_date": "2026-02-15",
  "category": "Software/Subscriptions",
  "status": "pending_approval",
  "approval_required": true,
  "approval_reason": "Amount exceeds $100 threshold",
  "file_path": "nerve_center/finances/invoices/inv_2026_001.pdf"
}
```

## Financial Safety Rules
- NEVER auto-pay any invoice
- ALWAYS verify vendor authenticity
- FLAG suspicious invoices (unexpected, unusually high, urgent payment requests)
- MAINTAIN audit trail for all financial actions
