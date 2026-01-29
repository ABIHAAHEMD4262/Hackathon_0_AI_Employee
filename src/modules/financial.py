"""
Financial Module
================
Financial tracking for invoices, expenses, revenue, and cash flow.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import hashlib


class InvoiceStatus(Enum):
    """Invoice status."""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


class ExpenseCategory(Enum):
    """Expense categories."""
    SOFTWARE = "software"
    MARKETING = "marketing"
    CONTRACTORS = "contractors"
    OFFICE = "office"
    TRAVEL = "travel"
    UTILITIES = "utilities"
    PROFESSIONAL = "professional"
    EQUIPMENT = "equipment"
    SUBSCRIPTIONS = "subscriptions"
    OTHER = "other"


class TransactionType(Enum):
    """Transaction types."""
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    REFUND = "refund"


@dataclass
class LineItem:
    """Invoice line item."""
    description: str
    quantity: float
    unit_price: float
    tax_rate: float = 0.0

    @property
    def subtotal(self) -> float:
        return self.quantity * self.unit_price

    @property
    def tax(self) -> float:
        return self.subtotal * self.tax_rate

    @property
    def total(self) -> float:
        return self.subtotal + self.tax

    def to_dict(self) -> Dict:
        return {
            "description": self.description,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "tax_rate": self.tax_rate,
            "subtotal": self.subtotal,
            "tax": self.tax,
            "total": self.total
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'LineItem':
        return cls(
            description=data["description"],
            quantity=data["quantity"],
            unit_price=data["unit_price"],
            tax_rate=data.get("tax_rate", 0.0)
        )


@dataclass
class Invoice:
    """Represents an invoice (sent or received)."""
    id: str
    number: str
    type: str  # 'sent' or 'received'

    # Parties
    from_name: str
    from_email: str
    to_name: str
    to_email: str

    # Amounts
    line_items: List[LineItem] = field(default_factory=list)
    currency: str = "USD"
    discount: float = 0.0

    # Dates
    issue_date: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    paid_date: Optional[datetime] = None

    # Status
    status: InvoiceStatus = InvoiceStatus.DRAFT

    # Additional info
    notes: str = ""
    payment_terms: str = "Net 30"
    payment_method: str = ""
    reference: str = ""

    # File reference
    file_path: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def subtotal(self) -> float:
        return sum(item.subtotal for item in self.line_items)

    @property
    def tax_total(self) -> float:
        return sum(item.tax for item in self.line_items)

    @property
    def total(self) -> float:
        return self.subtotal + self.tax_total - self.discount

    @property
    def is_overdue(self) -> bool:
        if self.status == InvoiceStatus.PAID:
            return False
        if not self.due_date:
            return False
        return datetime.now() > self.due_date

    @property
    def days_until_due(self) -> Optional[int]:
        if not self.due_date:
            return None
        delta = self.due_date - datetime.now()
        return delta.days

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "number": self.number,
            "type": self.type,
            "from_name": self.from_name,
            "from_email": self.from_email,
            "to_name": self.to_name,
            "to_email": self.to_email,
            "line_items": [item.to_dict() for item in self.line_items],
            "currency": self.currency,
            "discount": self.discount,
            "subtotal": self.subtotal,
            "tax_total": self.tax_total,
            "total": self.total,
            "issue_date": self.issue_date.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "paid_date": self.paid_date.isoformat() if self.paid_date else None,
            "status": self.status.value,
            "notes": self.notes,
            "payment_terms": self.payment_terms,
            "payment_method": self.payment_method,
            "reference": self.reference,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Invoice':
        return cls(
            id=data["id"],
            number=data["number"],
            type=data["type"],
            from_name=data["from_name"],
            from_email=data["from_email"],
            to_name=data["to_name"],
            to_email=data["to_email"],
            line_items=[LineItem.from_dict(i) for i in data.get("line_items", [])],
            currency=data.get("currency", "USD"),
            discount=data.get("discount", 0.0),
            issue_date=datetime.fromisoformat(data["issue_date"]) if data.get("issue_date") else datetime.now(),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            paid_date=datetime.fromisoformat(data["paid_date"]) if data.get("paid_date") else None,
            status=InvoiceStatus(data.get("status", "draft")),
            notes=data.get("notes", ""),
            payment_terms=data.get("payment_terms", "Net 30"),
            payment_method=data.get("payment_method", ""),
            reference=data.get("reference", ""),
            file_path=data.get("file_path"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            metadata=data.get("metadata", {})
        )


@dataclass
class Expense:
    """Represents an expense."""
    id: str
    description: str
    amount: float
    category: ExpenseCategory
    date: datetime
    vendor: str = ""
    is_recurring: bool = False
    recurring_frequency: str = ""  # monthly, yearly, etc.
    invoice_id: Optional[str] = None
    notes: str = ""
    receipt_path: Optional[str] = None
    approved: bool = False
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "category": self.category.value,
            "date": self.date.isoformat(),
            "vendor": self.vendor,
            "is_recurring": self.is_recurring,
            "recurring_frequency": self.recurring_frequency,
            "invoice_id": self.invoice_id,
            "notes": self.notes,
            "receipt_path": self.receipt_path,
            "approved": self.approved,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Expense':
        return cls(
            id=data["id"],
            description=data["description"],
            amount=data["amount"],
            category=ExpenseCategory(data.get("category", "other")),
            date=datetime.fromisoformat(data["date"]),
            vendor=data.get("vendor", ""),
            is_recurring=data.get("is_recurring", False),
            recurring_frequency=data.get("recurring_frequency", ""),
            invoice_id=data.get("invoice_id"),
            notes=data.get("notes", ""),
            receipt_path=data.get("receipt_path"),
            approved=data.get("approved", False),
            approved_by=data.get("approved_by", ""),
            approved_at=datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None,
            metadata=data.get("metadata", {})
        )


@dataclass
class Transaction:
    """Represents a financial transaction."""
    id: str
    type: TransactionType
    amount: float
    description: str
    date: datetime
    category: str = ""
    reference: str = ""
    related_invoice_id: Optional[str] = None
    related_expense_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "amount": self.amount,
            "description": self.description,
            "date": self.date.isoformat(),
            "category": self.category,
            "reference": self.reference,
            "related_invoice_id": self.related_invoice_id,
            "related_expense_id": self.related_expense_id,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        return cls(
            id=data["id"],
            type=TransactionType(data["type"]),
            amount=data["amount"],
            description=data["description"],
            date=datetime.fromisoformat(data["date"]),
            category=data.get("category", ""),
            reference=data.get("reference", ""),
            related_invoice_id=data.get("related_invoice_id"),
            related_expense_id=data.get("related_expense_id"),
            metadata=data.get("metadata", {})
        )


class FinancialModule:
    """
    Financial tracking module.

    Features:
    - Invoice management (sent and received)
    - Expense tracking
    - Transaction logging
    - Cash flow analysis
    - Budget tracking
    - Financial reporting
    """

    def __init__(self, data_path: str = "nerve_center/finances"):
        self.data_path = Path(data_path)
        self.invoices_file = self.data_path / "invoices.json"
        self.expenses_file = self.data_path / "expenses.json"
        self.transactions_file = self.data_path / "transactions.json"
        self.budgets_file = self.data_path / "budgets.json"

        self.invoices: Dict[str, Invoice] = {}
        self.expenses: Dict[str, Expense] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.budgets: Dict[str, Dict] = {}

        self.logger = logging.getLogger('Financial')

        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)
        (self.data_path / "invoices").mkdir(exist_ok=True)
        (self.data_path / "receipts").mkdir(exist_ok=True)

        # Load existing data
        self._load_data()

    def _load_data(self):
        """Load financial data from disk."""
        try:
            if self.invoices_file.exists():
                with open(self.invoices_file, 'r') as f:
                    data = json.load(f)
                    for inv in data:
                        invoice = Invoice.from_dict(inv)
                        self.invoices[invoice.id] = invoice

            if self.expenses_file.exists():
                with open(self.expenses_file, 'r') as f:
                    data = json.load(f)
                    for exp in data:
                        expense = Expense.from_dict(exp)
                        self.expenses[expense.id] = expense

            if self.transactions_file.exists():
                with open(self.transactions_file, 'r') as f:
                    data = json.load(f)
                    for txn in data:
                        transaction = Transaction.from_dict(txn)
                        self.transactions[transaction.id] = transaction

            if self.budgets_file.exists():
                with open(self.budgets_file, 'r') as f:
                    self.budgets = json.load(f)

            self.logger.info(f"Loaded {len(self.invoices)} invoices, {len(self.expenses)} expenses")

        except Exception as e:
            self.logger.error(f"Error loading financial data: {e}")

    def _save_data(self):
        """Save financial data to disk."""
        try:
            with open(self.invoices_file, 'w') as f:
                json.dump([inv.to_dict() for inv in self.invoices.values()], f, indent=2)

            with open(self.expenses_file, 'w') as f:
                json.dump([exp.to_dict() for exp in self.expenses.values()], f, indent=2)

            with open(self.transactions_file, 'w') as f:
                json.dump([txn.to_dict() for txn in self.transactions.values()], f, indent=2)

            with open(self.budgets_file, 'w') as f:
                json.dump(self.budgets, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving financial data: {e}")

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        hash_input = f"{prefix}-{datetime.now().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]

    def _generate_invoice_number(self, invoice_type: str) -> str:
        """Generate a unique invoice number."""
        year = datetime.now().year
        prefix = "INV" if invoice_type == "sent" else "BILL"
        count = len([i for i in self.invoices.values() if i.type == invoice_type]) + 1
        return f"{prefix}-{year}-{count:04d}"

    # Invoice Management
    def create_invoice(
        self,
        invoice_type: str,
        from_name: str,
        from_email: str,
        to_name: str,
        to_email: str,
        line_items: List[Dict],
        due_days: int = 30,
        **kwargs
    ) -> Invoice:
        """Create a new invoice."""
        invoice_id = self._generate_id("invoice")
        invoice_number = self._generate_invoice_number(invoice_type)

        items = [LineItem(**item) for item in line_items]

        due_date = datetime.now() + timedelta(days=due_days)

        invoice = Invoice(
            id=invoice_id,
            number=invoice_number,
            type=invoice_type,
            from_name=from_name,
            from_email=from_email,
            to_name=to_name,
            to_email=to_email,
            line_items=items,
            due_date=due_date,
            **kwargs
        )

        self.invoices[invoice_id] = invoice
        self._save_data()

        self.logger.info(f"Created invoice: {invoice_number} (${invoice.total:.2f})")
        return invoice

    def update_invoice_status(self, invoice_id: str, status: InvoiceStatus) -> Optional[Invoice]:
        """Update invoice status."""
        if invoice_id not in self.invoices:
            return None

        invoice = self.invoices[invoice_id]
        invoice.status = status
        invoice.updated_at = datetime.now()

        if status == InvoiceStatus.PAID:
            invoice.paid_date = datetime.now()
            # Create transaction
            self.add_transaction(
                type=TransactionType.INCOME if invoice.type == "sent" else TransactionType.EXPENSE,
                amount=invoice.total,
                description=f"Invoice {invoice.number}",
                related_invoice_id=invoice_id
            )

        self._save_data()
        return invoice

    def get_invoices(
        self,
        invoice_type: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        overdue_only: bool = False
    ) -> List[Invoice]:
        """Get invoices with filters."""
        results = []

        for invoice in self.invoices.values():
            if invoice_type and invoice.type != invoice_type:
                continue
            if status and invoice.status != status:
                continue
            if overdue_only and not invoice.is_overdue:
                continue
            results.append(invoice)

        return sorted(results, key=lambda x: x.issue_date, reverse=True)

    # Expense Management
    def add_expense(
        self,
        description: str,
        amount: float,
        category: ExpenseCategory,
        vendor: str = "",
        **kwargs
    ) -> Expense:
        """Add an expense."""
        expense_id = self._generate_id("expense")

        expense = Expense(
            id=expense_id,
            description=description,
            amount=amount,
            category=category,
            date=datetime.now(),
            vendor=vendor,
            **kwargs
        )

        self.expenses[expense_id] = expense

        # Create transaction
        self.add_transaction(
            type=TransactionType.EXPENSE,
            amount=amount,
            description=description,
            category=category.value,
            related_expense_id=expense_id
        )

        self._save_data()
        self.logger.info(f"Added expense: {description} (${amount:.2f})")
        return expense

    def approve_expense(self, expense_id: str, approved_by: str) -> Optional[Expense]:
        """Approve an expense."""
        if expense_id not in self.expenses:
            return None

        expense = self.expenses[expense_id]
        expense.approved = True
        expense.approved_by = approved_by
        expense.approved_at = datetime.now()

        self._save_data()
        return expense

    def get_expenses(
        self,
        category: Optional[ExpenseCategory] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        approved_only: bool = False
    ) -> List[Expense]:
        """Get expenses with filters."""
        results = []

        for expense in self.expenses.values():
            if category and expense.category != category:
                continue
            if start_date and expense.date < start_date:
                continue
            if end_date and expense.date > end_date:
                continue
            if approved_only and not expense.approved:
                continue
            results.append(expense)

        return sorted(results, key=lambda x: x.date, reverse=True)

    # Transaction Management
    def add_transaction(
        self,
        type: TransactionType,
        amount: float,
        description: str,
        **kwargs
    ) -> Transaction:
        """Add a transaction."""
        txn_id = self._generate_id("txn")

        transaction = Transaction(
            id=txn_id,
            type=type,
            amount=amount,
            description=description,
            date=datetime.now(),
            **kwargs
        )

        self.transactions[txn_id] = transaction
        self._save_data()
        return transaction

    def get_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        type: Optional[TransactionType] = None
    ) -> List[Transaction]:
        """Get transactions with filters."""
        results = []

        for txn in self.transactions.values():
            if start_date and txn.date < start_date:
                continue
            if end_date and txn.date > end_date:
                continue
            if type and txn.type != type:
                continue
            results.append(txn)

        return sorted(results, key=lambda x: x.date, reverse=True)

    # Budget Management
    def set_budget(self, category: str, monthly_amount: float, year: int = None):
        """Set a monthly budget for a category."""
        year = year or datetime.now().year
        key = f"{year}_{category}"
        self.budgets[key] = {
            "category": category,
            "year": year,
            "monthly_amount": monthly_amount,
            "set_at": datetime.now().isoformat()
        }
        self._save_data()

    def get_budget_status(self, month: int = None, year: int = None) -> Dict[str, Dict]:
        """Get budget status for a month."""
        month = month or datetime.now().month
        year = year or datetime.now().year

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # Get expenses by category
        expenses = self.get_expenses(start_date=start_date, end_date=end_date)
        spent_by_category: Dict[str, float] = {}
        for exp in expenses:
            cat = exp.category.value
            spent_by_category[cat] = spent_by_category.get(cat, 0) + exp.amount

        # Compare to budgets
        status = {}
        for key, budget in self.budgets.items():
            if str(year) in key:
                cat = budget["category"]
                monthly = budget["monthly_amount"]
                spent = spent_by_category.get(cat, 0)
                status[cat] = {
                    "budget": monthly,
                    "spent": spent,
                    "remaining": monthly - spent,
                    "percentage": (spent / monthly * 100) if monthly > 0 else 0
                }

        return status

    # Reporting
    def get_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get financial summary."""
        if not start_date:
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        if not end_date:
            end_date = datetime.now()

        invoices_sent = self.get_invoices(invoice_type="sent")
        invoices_received = self.get_invoices(invoice_type="received")
        transactions = self.get_transactions(start_date=start_date, end_date=end_date)

        revenue = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
        expenses = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)

        outstanding_ar = sum(
            i.total for i in invoices_sent
            if i.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
        )
        outstanding_ap = sum(
            i.total for i in invoices_received
            if i.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
        )

        overdue_ar = sum(
            i.total for i in invoices_sent
            if i.is_overdue
        )
        overdue_ap = sum(
            i.total for i in invoices_received
            if i.is_overdue
        )

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "revenue": revenue,
            "expenses": expenses,
            "net_profit": revenue - expenses,
            "profit_margin": ((revenue - expenses) / revenue * 100) if revenue > 0 else 0,
            "accounts_receivable": outstanding_ar,
            "accounts_payable": outstanding_ap,
            "overdue_receivables": overdue_ar,
            "overdue_payables": overdue_ap,
            "invoices_sent_count": len([i for i in invoices_sent if i.issue_date >= start_date]),
            "invoices_received_count": len([i for i in invoices_received if i.issue_date >= start_date]),
            "expense_count": len([e for e in self.expenses.values() if e.date >= start_date])
        }

    def get_cash_flow_projection(self, months: int = 6) -> List[Dict]:
        """Project cash flow for upcoming months."""
        projection = []
        current_date = datetime.now()

        for i in range(months):
            month_date = current_date.replace(day=1) + timedelta(days=32 * i)
            month_date = month_date.replace(day=1)

            # Expected income from outstanding invoices
            expected_income = sum(
                i.total for i in self.invoices.values()
                if i.type == "sent"
                and i.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
                and i.due_date
                and i.due_date.month == month_date.month
                and i.due_date.year == month_date.year
            )

            # Expected expenses from outstanding bills
            expected_expenses = sum(
                i.total for i in self.invoices.values()
                if i.type == "received"
                and i.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
                and i.due_date
                and i.due_date.month == month_date.month
                and i.due_date.year == month_date.year
            )

            # Add recurring expenses
            for exp in self.expenses.values():
                if exp.is_recurring:
                    expected_expenses += exp.amount

            projection.append({
                "month": month_date.strftime("%Y-%m"),
                "expected_income": expected_income,
                "expected_expenses": expected_expenses,
                "net": expected_income - expected_expenses
            })

        return projection
