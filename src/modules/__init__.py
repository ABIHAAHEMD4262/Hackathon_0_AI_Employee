"""
AI Employee Modules Package
===========================
Business logic modules for the AI Employee system.
"""

from .crm import CRMModule, Contact, Interaction
from .financial import FinancialModule, Invoice, Expense, Transaction
from .projects import ProjectModule, Project, Task, Milestone
from .analytics import AnalyticsModule

__all__ = [
    'CRMModule',
    'Contact',
    'Interaction',
    'FinancialModule',
    'Invoice',
    'Expense',
    'Transaction',
    'ProjectModule',
    'Project',
    'Task',
    'Milestone',
    'AnalyticsModule',
]
