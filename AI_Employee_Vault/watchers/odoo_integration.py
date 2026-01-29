"""
Odoo Accounting Integration
MCP Server for Odoo JSON-RPC APIs
Handles invoices, contacts, expenses, and financial reporting
"""

import os
import json
import xmlrpc.client
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

load_dotenv()


class OdooClient:
    """
    Odoo JSON-RPC Client for accounting operations
    Supports Odoo 14+ versions
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs = self.vault_path / 'Logs'
        self.logs.mkdir(exist_ok=True)

        # Odoo connection settings
        self.url = os.getenv('ODOO_URL', 'https://your-company.odoo.com')
        self.db = os.getenv('ODOO_DB', 'your-database')
        self.username = os.getenv('ODOO_USERNAME', '')
        self.password = os.getenv('ODOO_API_KEY', '')  # Use API key, not password

        # XML-RPC endpoints
        self.common = None
        self.models = None
        self.uid = None

        self.log("Odoo Client initialized")

    def log(self, message: str, level: str = 'INFO'):
        """Log message"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [Odoo] [{level}] {message}"
        print(log_entry)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'odoo_{today}.log'
        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')

    def connect(self) -> bool:
        """Establish connection to Odoo"""
        try:
            # Common endpoint for authentication
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')

            # Check server version
            version = self.common.version()
            self.log(f"Connected to Odoo {version.get('server_version', 'unknown')}")

            # Authenticate
            self.uid = self.common.authenticate(
                self.db,
                self.username,
                self.password,
                {}
            )

            if not self.uid:
                self.log("Authentication failed", 'ERROR')
                return False

            # Models endpoint for operations
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

            self.log(f"Authenticated as user ID: {self.uid}")
            return True

        except Exception as e:
            self.log(f"Connection error: {e}", 'ERROR')
            return False

    def execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """Execute Odoo method"""
        if not self.uid or not self.models:
            if not self.connect():
                raise ConnectionError("Not connected to Odoo")

        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            model,
            method,
            args,
            kwargs
        )

    # ==================== CONTACTS ====================

    def search_contacts(self, domain: List = None, limit: int = 100) -> List[Dict]:
        """Search for contacts/partners"""
        domain = domain or []

        ids = self.execute('res.partner', 'search', domain, limit=limit)
        if not ids:
            return []

        contacts = self.execute('res.partner', 'read', ids, {
            'fields': ['name', 'email', 'phone', 'mobile', 'street', 'city',
                      'country_id', 'is_company', 'customer_rank', 'supplier_rank']
        })

        self.log(f"Found {len(contacts)} contacts")
        return contacts

    def create_contact(self, data: Dict) -> int:
        """Create a new contact"""
        required_fields = ['name']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        contact_id = self.execute('res.partner', 'create', [data])
        self.log(f"Created contact ID: {contact_id}")
        return contact_id

    def get_contact(self, contact_id: int) -> Optional[Dict]:
        """Get contact by ID"""
        contacts = self.execute('res.partner', 'read', [contact_id])
        return contacts[0] if contacts else None

    # ==================== INVOICES ====================

    def search_invoices(self, state: str = None, limit: int = 100) -> List[Dict]:
        """Search for invoices"""
        domain = [('move_type', 'in', ['out_invoice', 'out_refund'])]

        if state:
            domain.append(('state', '=', state))

        ids = self.execute('account.move', 'search', domain, limit=limit)
        if not ids:
            return []

        invoices = self.execute('account.move', 'read', ids, {
            'fields': ['name', 'partner_id', 'invoice_date', 'invoice_date_due',
                      'amount_total', 'amount_residual', 'state', 'payment_state']
        })

        self.log(f"Found {len(invoices)} invoices")
        return invoices

    def create_invoice(self, partner_id: int, lines: List[Dict],
                       invoice_date: str = None) -> int:
        """
        Create a new customer invoice

        Args:
            partner_id: Customer ID
            lines: List of invoice lines [{'product_id': 1, 'quantity': 1, 'price_unit': 100}]
            invoice_date: Invoice date (YYYY-MM-DD)
        """
        invoice_data = {
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_date': invoice_date or datetime.now().strftime('%Y-%m-%d'),
            'invoice_line_ids': []
        }

        # Add invoice lines
        for line in lines:
            invoice_data['invoice_line_ids'].append((0, 0, {
                'name': line.get('description', 'Service'),
                'quantity': line.get('quantity', 1),
                'price_unit': line.get('price_unit', 0),
                'product_id': line.get('product_id'),
            }))

        invoice_id = self.execute('account.move', 'create', [invoice_data])
        self.log(f"Created invoice ID: {invoice_id}")
        return invoice_id

    def post_invoice(self, invoice_id: int) -> bool:
        """Post/confirm an invoice"""
        try:
            self.execute('account.move', 'action_post', [[invoice_id]])
            self.log(f"Posted invoice ID: {invoice_id}")
            return True
        except Exception as e:
            self.log(f"Failed to post invoice: {e}", 'ERROR')
            return False

    def get_overdue_invoices(self) -> List[Dict]:
        """Get all overdue invoices"""
        today = datetime.now().strftime('%Y-%m-%d')
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid'),
            ('invoice_date_due', '<', today)
        ]

        ids = self.execute('account.move', 'search', domain)
        if not ids:
            return []

        invoices = self.execute('account.move', 'read', ids, {
            'fields': ['name', 'partner_id', 'invoice_date_due',
                      'amount_total', 'amount_residual']
        })

        self.log(f"Found {len(invoices)} overdue invoices")
        return invoices

    # ==================== EXPENSES ====================

    def search_expenses(self, state: str = None, limit: int = 100) -> List[Dict]:
        """Search for expenses"""
        domain = []
        if state:
            domain.append(('state', '=', state))

        ids = self.execute('hr.expense', 'search', domain, limit=limit)
        if not ids:
            return []

        expenses = self.execute('hr.expense', 'read', ids, {
            'fields': ['name', 'employee_id', 'date', 'total_amount',
                      'state', 'description', 'product_id']
        })

        self.log(f"Found {len(expenses)} expenses")
        return expenses

    def create_expense(self, data: Dict) -> int:
        """Create a new expense"""
        expense_data = {
            'name': data.get('name', 'Expense'),
            'employee_id': data.get('employee_id'),
            'product_id': data.get('product_id'),
            'total_amount': data.get('amount', 0),
            'date': data.get('date', datetime.now().strftime('%Y-%m-%d')),
            'description': data.get('description', ''),
        }

        expense_id = self.execute('hr.expense', 'create', [expense_data])
        self.log(f"Created expense ID: {expense_id}")
        return expense_id

    # ==================== PRODUCTS ====================

    def search_products(self, name: str = None, limit: int = 100) -> List[Dict]:
        """Search for products"""
        domain = []
        if name:
            domain.append(('name', 'ilike', name))

        ids = self.execute('product.product', 'search', domain, limit=limit)
        if not ids:
            return []

        products = self.execute('product.product', 'read', ids, {
            'fields': ['name', 'default_code', 'list_price', 'standard_price',
                      'type', 'categ_id', 'qty_available']
        })

        return products

    # ==================== REPORTS ====================

    def get_financial_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get financial summary for a date range"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Get invoices in range
        invoice_domain = [
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date)
        ]

        invoice_ids = self.execute('account.move', 'search', invoice_domain)
        invoices = []
        if invoice_ids:
            invoices = self.execute('account.move', 'read', invoice_ids, {
                'fields': ['amount_total', 'amount_residual', 'state', 'payment_state']
            })

        # Calculate totals
        total_invoiced = sum(inv['amount_total'] for inv in invoices)
        total_paid = sum(
            inv['amount_total'] - inv['amount_residual']
            for inv in invoices
            if inv['state'] == 'posted'
        )
        total_outstanding = sum(
            inv['amount_residual']
            for inv in invoices
            if inv['state'] == 'posted' and inv['payment_state'] != 'paid'
        )

        # Get bills (vendor invoices)
        bill_domain = [
            ('move_type', '=', 'in_invoice'),
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date)
        ]

        bill_ids = self.execute('account.move', 'search', bill_domain)
        bills = []
        if bill_ids:
            bills = self.execute('account.move', 'read', bill_ids, {
                'fields': ['amount_total', 'state']
            })

        total_bills = sum(bill['amount_total'] for bill in bills)

        summary = {
            'period': f'{start_date} to {end_date}',
            'invoices': {
                'count': len(invoices),
                'total_invoiced': total_invoiced,
                'total_paid': total_paid,
                'total_outstanding': total_outstanding
            },
            'bills': {
                'count': len(bills),
                'total': total_bills
            },
            'net_income': total_paid - total_bills
        }

        self.log(f"Generated financial summary for {summary['period']}")
        return summary

    def generate_aging_report(self) -> Dict:
        """Generate accounts receivable aging report"""
        today = datetime.now()

        # Get all unpaid invoices
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', '!=', 'paid')
        ]

        ids = self.execute('account.move', 'search', domain)
        if not ids:
            return {'buckets': {}, 'total': 0}

        invoices = self.execute('account.move', 'read', ids, {
            'fields': ['name', 'partner_id', 'invoice_date_due', 'amount_residual']
        })

        # Age buckets
        buckets = {
            'current': [],      # Not due yet
            '1-30': [],         # 1-30 days overdue
            '31-60': [],        # 31-60 days overdue
            '61-90': [],        # 61-90 days overdue
            '90+': []           # Over 90 days overdue
        }

        for inv in invoices:
            due_date = datetime.strptime(inv['invoice_date_due'], '%Y-%m-%d')
            days_overdue = (today - due_date).days

            inv_data = {
                'name': inv['name'],
                'partner': inv['partner_id'][1] if inv['partner_id'] else 'Unknown',
                'amount': inv['amount_residual'],
                'due_date': inv['invoice_date_due'],
                'days_overdue': days_overdue
            }

            if days_overdue <= 0:
                buckets['current'].append(inv_data)
            elif days_overdue <= 30:
                buckets['1-30'].append(inv_data)
            elif days_overdue <= 60:
                buckets['31-60'].append(inv_data)
            elif days_overdue <= 90:
                buckets['61-90'].append(inv_data)
            else:
                buckets['90+'].append(inv_data)

        # Calculate totals per bucket
        totals = {
            bucket: sum(inv['amount'] for inv in invs)
            for bucket, invs in buckets.items()
        }

        report = {
            'generated_at': today.isoformat(),
            'buckets': buckets,
            'totals': totals,
            'grand_total': sum(totals.values())
        }

        self.log("Generated aging report")
        return report


class OdooMCPServer:
    """
    MCP Server wrapper for Odoo operations
    Provides JSON-RPC interface for Claude Code
    """

    def __init__(self, vault_path: str):
        self.client = OdooClient(vault_path)
        self.vault_path = Path(vault_path)

    def handle_request(self, request: Dict) -> Dict:
        """Handle MCP request"""
        method = request.get('method', '')
        params = request.get('params', {})

        handlers = {
            # Contacts
            'search_contacts': self.client.search_contacts,
            'create_contact': self.client.create_contact,
            'get_contact': self.client.get_contact,

            # Invoices
            'search_invoices': self.client.search_invoices,
            'create_invoice': self.client.create_invoice,
            'post_invoice': self.client.post_invoice,
            'get_overdue_invoices': self.client.get_overdue_invoices,

            # Expenses
            'search_expenses': self.client.search_expenses,
            'create_expense': self.client.create_expense,

            # Products
            'search_products': self.client.search_products,

            # Reports
            'get_financial_summary': self.client.get_financial_summary,
            'generate_aging_report': self.client.generate_aging_report,
        }

        if method not in handlers:
            return {'error': f'Unknown method: {method}'}

        try:
            result = handlers[method](**params)
            return {'result': result}
        except Exception as e:
            return {'error': str(e)}

    def create_invoice_approval(self, partner_name: str, amount: float,
                                 description: str) -> Path:
        """Create an invoice approval request"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"invoice-approval-{timestamp}.md"
        filepath = self.vault_path / 'Approvals' / filename

        content = f"""---
type: invoice_approval
partner: {partner_name}
amount: {amount}
created: {datetime.now().isoformat()}
status: pending
---

# Invoice Approval Request

## Details
- **Customer**: {partner_name}
- **Amount**: ${amount:.2f}
- **Description**: {description}
- **Created**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Action Required
Please review and approve this invoice to be created in Odoo.

---

*This invoice was prepared by AI Employee. Please review before approving.*
"""

        filepath.write_text(content, encoding='utf-8')
        self.client.log(f"Created invoice approval: {filename}")
        return filepath


def main():
    """Main entry point"""
    import sys

    load_dotenv()

    vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent))

    print("=" * 50)
    print("  Odoo Accounting Integration")
    print("=" * 50)
    print(f"Vault: {vault_path}")
    print()

    client = OdooClient(vault_path)

    if '--test' in sys.argv or '-t' in sys.argv:
        print("Testing Odoo connection...")

        if client.connect():
            print("\n[SUCCESS] Connected to Odoo!")

            # Test operations
            print("\nTesting operations:")

            # Search contacts
            contacts = client.search_contacts(limit=5)
            print(f"  - Found {len(contacts)} contacts")

            # Search invoices
            invoices = client.search_invoices(limit=5)
            print(f"  - Found {len(invoices)} invoices")

            # Get financial summary
            summary = client.get_financial_summary()
            print(f"  - Financial summary: {summary['period']}")
            print(f"    Invoiced: ${summary['invoices']['total_invoiced']:.2f}")
            print(f"    Outstanding: ${summary['invoices']['total_outstanding']:.2f}")

        else:
            print("\n[ERROR] Failed to connect to Odoo")
            print("Please check your .env configuration:")
            print("  ODOO_URL=https://your-company.odoo.com")
            print("  ODOO_DB=your-database")
            print("  ODOO_USERNAME=your-email@example.com")
            print("  ODOO_API_KEY=your-api-key")

    elif '--summary' in sys.argv:
        if client.connect():
            summary = client.get_financial_summary()
            print(json.dumps(summary, indent=2))

    elif '--aging' in sys.argv:
        if client.connect():
            report = client.generate_aging_report()
            print(json.dumps(report, indent=2, default=str))

    elif '--overdue' in sys.argv:
        if client.connect():
            invoices = client.get_overdue_invoices()
            print(f"\nOverdue Invoices ({len(invoices)}):")
            for inv in invoices:
                print(f"  - {inv['name']}: ${inv['amount_residual']:.2f} (due: {inv['invoice_date_due']})")

    else:
        print("Usage:")
        print("  python odoo_integration.py --test     Test Odoo connection")
        print("  python odoo_integration.py --summary  Get financial summary")
        print("  python odoo_integration.py --aging    Generate aging report")
        print("  python odoo_integration.py --overdue  List overdue invoices")
        print()
        print("Environment variables required:")
        print("  ODOO_URL       - Odoo server URL")
        print("  ODOO_DB        - Database name")
        print("  ODOO_USERNAME  - Username/email")
        print("  ODOO_API_KEY   - API key (not password)")


if __name__ == '__main__':
    main()
