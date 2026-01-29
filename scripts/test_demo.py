#!/usr/bin/env python3
"""
AI Employee Test Demo Script
============================
This script populates the system with test data so you can see
the Dashboard in action without setting up real integrations.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Setup paths
NERVE_CENTER = Path(__file__).parent.parent / "nerve_center"
DATA_PATHS = {
    "crm": NERVE_CENTER / "crm",
    "finances": NERVE_CENTER / "finances",
    "projects": NERVE_CENTER / "projects",
    "analytics": NERVE_CENTER / "analytics",
    "inbox": NERVE_CENTER / "inbox",
    "logs": NERVE_CENTER / "logs",
}

# Create directories
for path in DATA_PATHS.values():
    path.mkdir(parents=True, exist_ok=True)


def create_test_contacts():
    """Create sample CRM contacts."""
    contacts = [
        {
            "id": "contact_001",
            "name": "John Smith",
            "email": "john.smith@acmecorp.com",
            "type": "client",
            "status": "active",
            "company": "Acme Corporation",
            "title": "CEO",
            "phone": "+1-555-0101",
            "lead_stage": None,
            "lead_value": 0,
            "tags": ["enterprise", "priority"],
            "is_vip": True,
            "last_contact": (datetime.now() - timedelta(days=2)).isoformat(),
            "next_follow_up": (datetime.now() + timedelta(days=3)).isoformat(),
            "created_at": (datetime.now() - timedelta(days=90)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source": "referral"
        },
        {
            "id": "contact_002",
            "name": "Sarah Johnson",
            "email": "sarah@techstartup.io",
            "type": "lead",
            "status": "active",
            "company": "Tech Startup Inc",
            "title": "CTO",
            "phone": "+1-555-0102",
            "lead_stage": "proposal",
            "lead_value": 15000,
            "tags": ["startup", "saas"],
            "is_vip": False,
            "last_contact": (datetime.now() - timedelta(days=5)).isoformat(),
            "next_follow_up": (datetime.now() + timedelta(days=1)).isoformat(),
            "created_at": (datetime.now() - timedelta(days=14)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source": "website"
        },
        {
            "id": "contact_003",
            "name": "Mike Chen",
            "email": "mike@designagency.com",
            "type": "partner",
            "status": "active",
            "company": "Design Agency Co",
            "title": "Creative Director",
            "phone": "+1-555-0103",
            "lead_stage": None,
            "lead_value": 0,
            "tags": ["design", "partner"],
            "is_vip": True,
            "last_contact": (datetime.now() - timedelta(days=35)).isoformat(),
            "next_follow_up": None,
            "created_at": (datetime.now() - timedelta(days=180)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source": "conference"
        },
        {
            "id": "contact_004",
            "name": "Emily Davis",
            "email": "emily@newclient.com",
            "type": "lead",
            "status": "active",
            "company": "New Client LLC",
            "title": "Marketing Manager",
            "phone": "+1-555-0104",
            "lead_stage": "qualified",
            "lead_value": 8000,
            "tags": ["marketing", "small-business"],
            "is_vip": False,
            "last_contact": (datetime.now() - timedelta(hours=3)).isoformat(),
            "next_follow_up": (datetime.now() + timedelta(days=2)).isoformat(),
            "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source": "linkedin"
        },
        {
            "id": "contact_005",
            "name": "David Wilson",
            "email": "david@bigenterprise.com",
            "type": "lead",
            "status": "active",
            "company": "Big Enterprise Inc",
            "title": "VP of Operations",
            "phone": "+1-555-0105",
            "lead_stage": "negotiation",
            "lead_value": 50000,
            "tags": ["enterprise", "high-value"],
            "is_vip": True,
            "last_contact": (datetime.now() - timedelta(days=1)).isoformat(),
            "next_follow_up": datetime.now().isoformat(),
            "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
            "updated_at": datetime.now().isoformat(),
            "source": "cold-outreach"
        }
    ]

    with open(DATA_PATHS["crm"] / "contacts.json", "w") as f:
        json.dump(contacts, f, indent=2)

    print(f"✓ Created {len(contacts)} test contacts")
    return contacts


def create_test_invoices():
    """Create sample invoices."""
    invoices = [
        {
            "id": "inv_001",
            "number": "INV-2026-0001",
            "type": "sent",
            "from_name": "Your Company",
            "from_email": "billing@yourcompany.com",
            "to_name": "Acme Corporation",
            "to_email": "ap@acmecorp.com",
            "line_items": [
                {"description": "Web Development Services - January", "quantity": 40, "unit_price": 150, "tax_rate": 0}
            ],
            "currency": "USD",
            "discount": 0,
            "issue_date": (datetime.now() - timedelta(days=15)).isoformat(),
            "due_date": (datetime.now() + timedelta(days=15)).isoformat(),
            "paid_date": None,
            "status": "sent",
            "notes": "Thank you for your business!",
            "payment_terms": "Net 30",
            "created_at": (datetime.now() - timedelta(days=15)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "inv_002",
            "number": "INV-2026-0002",
            "type": "sent",
            "from_name": "Your Company",
            "from_email": "billing@yourcompany.com",
            "to_name": "Tech Startup Inc",
            "to_email": "finance@techstartup.io",
            "line_items": [
                {"description": "Consulting - Strategy Session", "quantity": 8, "unit_price": 200, "tax_rate": 0},
                {"description": "Implementation Support", "quantity": 16, "unit_price": 150, "tax_rate": 0}
            ],
            "currency": "USD",
            "discount": 200,
            "issue_date": (datetime.now() - timedelta(days=5)).isoformat(),
            "due_date": (datetime.now() + timedelta(days=25)).isoformat(),
            "paid_date": None,
            "status": "sent",
            "notes": "",
            "payment_terms": "Net 30",
            "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "inv_003",
            "number": "INV-2026-0003",
            "type": "sent",
            "from_name": "Your Company",
            "from_email": "billing@yourcompany.com",
            "to_name": "Old Client Co",
            "to_email": "payments@oldclient.com",
            "line_items": [
                {"description": "Monthly Retainer - December", "quantity": 1, "unit_price": 3000, "tax_rate": 0}
            ],
            "currency": "USD",
            "discount": 0,
            "issue_date": (datetime.now() - timedelta(days=45)).isoformat(),
            "due_date": (datetime.now() - timedelta(days=15)).isoformat(),
            "paid_date": None,
            "status": "overdue",
            "notes": "",
            "payment_terms": "Net 30",
            "created_at": (datetime.now() - timedelta(days=45)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "bill_001",
            "number": "BILL-2026-0001",
            "type": "received",
            "from_name": "AWS",
            "from_email": "billing@aws.amazon.com",
            "to_name": "Your Company",
            "to_email": "you@yourcompany.com",
            "line_items": [
                {"description": "AWS Services - January", "quantity": 1, "unit_price": 287.45, "tax_rate": 0}
            ],
            "currency": "USD",
            "discount": 0,
            "issue_date": (datetime.now() - timedelta(days=3)).isoformat(),
            "due_date": (datetime.now() + timedelta(days=27)).isoformat(),
            "paid_date": None,
            "status": "sent",
            "notes": "",
            "payment_terms": "Net 30",
            "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "bill_002",
            "number": "BILL-2026-0002",
            "type": "received",
            "from_name": "Contractor Jane",
            "from_email": "jane@freelancer.com",
            "to_name": "Your Company",
            "to_email": "you@yourcompany.com",
            "line_items": [
                {"description": "Design Work - Landing Pages", "quantity": 20, "unit_price": 75, "tax_rate": 0}
            ],
            "currency": "USD",
            "discount": 0,
            "issue_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "paid_date": None,
            "status": "sent",
            "notes": "Pending approval",
            "payment_terms": "Net 14",
            "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]

    with open(DATA_PATHS["finances"] / "invoices.json", "w") as f:
        json.dump(invoices, f, indent=2)

    print(f"✓ Created {len(invoices)} test invoices")
    return invoices


def create_test_expenses():
    """Create sample expenses."""
    expenses = [
        {
            "id": "exp_001",
            "description": "Notion Subscription",
            "amount": 16.00,
            "category": "subscriptions",
            "date": datetime.now().isoformat(),
            "vendor": "Notion",
            "is_recurring": True,
            "recurring_frequency": "monthly",
            "approved": True
        },
        {
            "id": "exp_002",
            "description": "GitHub Team",
            "amount": 44.00,
            "category": "software",
            "date": datetime.now().isoformat(),
            "vendor": "GitHub",
            "is_recurring": True,
            "recurring_frequency": "monthly",
            "approved": True
        },
        {
            "id": "exp_003",
            "description": "Google Workspace",
            "amount": 18.00,
            "category": "software",
            "date": datetime.now().isoformat(),
            "vendor": "Google",
            "is_recurring": True,
            "recurring_frequency": "monthly",
            "approved": True
        },
        {
            "id": "exp_004",
            "description": "Facebook Ads - January Campaign",
            "amount": 500.00,
            "category": "marketing",
            "date": (datetime.now() - timedelta(days=5)).isoformat(),
            "vendor": "Meta",
            "is_recurring": False,
            "approved": True
        },
        {
            "id": "exp_005",
            "description": "New Monitor",
            "amount": 349.99,
            "category": "equipment",
            "date": (datetime.now() - timedelta(days=10)).isoformat(),
            "vendor": "Amazon",
            "is_recurring": False,
            "approved": False
        }
    ]

    with open(DATA_PATHS["finances"] / "expenses.json", "w") as f:
        json.dump(expenses, f, indent=2)

    print(f"✓ Created {len(expenses)} test expenses")
    return expenses


def create_test_projects():
    """Create sample projects and tasks."""
    projects = [
        {
            "id": "proj_001",
            "name": "Website Redesign",
            "description": "Complete redesign of company website",
            "client": "Acme Corporation",
            "status": "active",
            "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "deadline": (datetime.now() + timedelta(days=30)).isoformat(),
            "budget": 15000,
            "budget_spent": 6000,
            "created_at": (datetime.now() - timedelta(days=30)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "proj_002",
            "name": "Mobile App MVP",
            "description": "Build MVP for mobile application",
            "client": "Tech Startup Inc",
            "status": "active",
            "start_date": (datetime.now() - timedelta(days=14)).isoformat(),
            "deadline": (datetime.now() + timedelta(days=60)).isoformat(),
            "budget": 25000,
            "budget_spent": 5000,
            "created_at": (datetime.now() - timedelta(days=14)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "proj_003",
            "name": "Marketing Automation",
            "description": "Set up email marketing automation",
            "client": "Internal",
            "status": "planning",
            "start_date": None,
            "deadline": (datetime.now() + timedelta(days=45)).isoformat(),
            "budget": 5000,
            "budget_spent": 0,
            "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]

    tasks = [
        # Website Redesign tasks
        {
            "id": "task_001",
            "title": "Finalize wireframes",
            "description": "Complete all page wireframes for client review",
            "project_id": "proj_001",
            "status": "completed",
            "priority": 2,
            "due_date": (datetime.now() - timedelta(days=10)).isoformat(),
            "completed_at": (datetime.now() - timedelta(days=12)).isoformat(),
            "estimated_hours": 8,
            "actual_hours": 6,
            "created_at": (datetime.now() - timedelta(days=25)).isoformat(),
            "updated_at": (datetime.now() - timedelta(days=12)).isoformat()
        },
        {
            "id": "task_002",
            "title": "Design homepage mockup",
            "description": "Create high-fidelity homepage design",
            "project_id": "proj_001",
            "status": "in_progress",
            "priority": 2,
            "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "completed_at": None,
            "estimated_hours": 12,
            "actual_hours": 8,
            "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "task_003",
            "title": "Client feedback review",
            "description": "Review and address client feedback on designs",
            "project_id": "proj_001",
            "status": "todo",
            "priority": 3,
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "completed_at": None,
            "estimated_hours": 4,
            "actual_hours": 0,
            "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "task_004",
            "title": "Implement responsive navigation",
            "description": "Build mobile-responsive navigation component",
            "project_id": "proj_001",
            "status": "blocked",
            "priority": 2,
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "completed_at": None,
            "estimated_hours": 6,
            "actual_hours": 0,
            "blocked_by": ["task_002"],
            "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        # Mobile App tasks
        {
            "id": "task_005",
            "title": "Set up React Native project",
            "description": "Initialize project with proper structure",
            "project_id": "proj_002",
            "status": "completed",
            "priority": 1,
            "due_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "completed_at": (datetime.now() - timedelta(days=8)).isoformat(),
            "estimated_hours": 4,
            "actual_hours": 3,
            "created_at": (datetime.now() - timedelta(days=14)).isoformat(),
            "updated_at": (datetime.now() - timedelta(days=8)).isoformat()
        },
        {
            "id": "task_006",
            "title": "Build authentication flow",
            "description": "Implement login/signup screens",
            "project_id": "proj_002",
            "status": "in_progress",
            "priority": 1,
            "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "completed_at": None,
            "estimated_hours": 16,
            "actual_hours": 10,
            "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "task_007",
            "title": "API integration",
            "description": "Connect app to backend API",
            "project_id": "proj_002",
            "status": "todo",
            "priority": 2,
            "due_date": (datetime.now() + timedelta(days=10)).isoformat(),
            "completed_at": None,
            "estimated_hours": 20,
            "actual_hours": 0,
            "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        # Overdue task
        {
            "id": "task_008",
            "title": "Update portfolio website",
            "description": "Add recent projects to portfolio",
            "project_id": None,
            "status": "todo",
            "priority": 4,
            "due_date": (datetime.now() - timedelta(days=3)).isoformat(),
            "completed_at": None,
            "estimated_hours": 2,
            "actual_hours": 0,
            "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        # Today's tasks
        {
            "id": "task_009",
            "title": "Weekly team standup",
            "description": "Conduct weekly team meeting",
            "project_id": None,
            "status": "todo",
            "priority": 2,
            "due_date": datetime.now().isoformat(),
            "completed_at": None,
            "estimated_hours": 1,
            "actual_hours": 0,
            "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": "task_010",
            "title": "Review pull requests",
            "description": "Review and merge pending PRs",
            "project_id": None,
            "status": "todo",
            "priority": 3,
            "due_date": datetime.now().isoformat(),
            "completed_at": None,
            "estimated_hours": 2,
            "actual_hours": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]

    with open(DATA_PATHS["projects"] / "projects.json", "w") as f:
        json.dump(projects, f, indent=2)

    with open(DATA_PATHS["projects"] / "tasks.json", "w") as f:
        json.dump(tasks, f, indent=2)

    print(f"✓ Created {len(projects)} test projects")
    print(f"✓ Created {len(tasks)} test tasks")
    return projects, tasks


def create_test_events():
    """Create sample inbox events for processing."""
    events = [
        {
            "id": "evt_001",
            "type": "email_received",
            "source": "gmail",
            "channel": "email",
            "timestamp": datetime.now().isoformat(),
            "priority": 2,
            "data": {
                "from": "john.smith@acmecorp.com",
                "from_name": "John Smith",
                "subject": "Re: Project Update - Urgent",
                "snippet": "Hi, I wanted to follow up on the project timeline. Can we schedule a call today?"
            }
        },
        {
            "id": "evt_002",
            "type": "whatsapp_message",
            "source": "whatsapp",
            "channel": "whatsapp",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "priority": 3,
            "data": {
                "from": "+1-555-0101",
                "from_name": "Sarah Johnson",
                "body": "Hey! Got the proposal. Looking good, will review and get back to you."
            }
        },
        {
            "id": "evt_003",
            "type": "invoice_detected",
            "source": "filesystem",
            "channel": "filesystem",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "priority": 2,
            "requires_approval": True,
            "data": {
                "filename": "invoice_contractor_jan2026.pdf",
                "filepath": "nerve_center/inbox/invoice_contractor_jan2026.pdf",
                "vendor": "Contractor Jane",
                "amount": 1500.00
            }
        },
        {
            "id": "evt_004",
            "type": "slack_message",
            "source": "slack",
            "channel": "slack",
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "priority": 4,
            "data": {
                "channel_name": "#general",
                "user_name": "TeamMember",
                "text": "Just pushed the latest changes. Ready for review!",
                "is_mention": False
            }
        },
        {
            "id": "evt_005",
            "type": "calendar_reminder",
            "source": "calendar",
            "channel": "calendar",
            "timestamp": datetime.now().isoformat(),
            "priority": 2,
            "data": {
                "summary": "Client Call - Acme Corporation",
                "start": (datetime.now() + timedelta(hours=2)).isoformat(),
                "minutes_until": 120
            }
        }
    ]

    # Save events to inbox
    for event in events:
        event_file = DATA_PATHS["inbox"] / f"{event['id']}.json"
        with open(event_file, "w") as f:
            json.dump(event, f, indent=2)

    print(f"✓ Created {len(events)} test events in inbox")
    return events


def create_test_activity_log():
    """Create sample activity log."""
    activities = [
        {
            "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
            "category": "email",
            "action": "Processed email from john@client.com",
            "status": "completed"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
            "category": "invoice",
            "action": "Created invoice INV-2026-0002",
            "status": "completed"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
            "category": "calendar",
            "action": "Scheduled meeting with Tech Startup",
            "status": "completed"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "category": "task",
            "action": "Completed task: Finalize wireframes",
            "status": "completed"
        },
        {
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "category": "whatsapp",
            "action": "Received message from Sarah Johnson",
            "status": "pending_response"
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "category": "slack",
            "action": "Processed Slack mention in #general",
            "status": "completed"
        },
        {
            "timestamp": datetime.now().isoformat(),
            "category": "system",
            "action": "Dashboard refreshed",
            "status": "completed"
        }
    ]

    with open(DATA_PATHS["logs"] / "activity.json", "w") as f:
        json.dump(activities, f, indent=2)

    print(f"✓ Created {len(activities)} activity log entries")
    return activities


def create_test_stats():
    """Create sample statistics for dashboard."""
    stats = {
        datetime.now().isoformat(): {
            "uptime_seconds": 28800,  # 8 hours
            "events_processed": 47,
            "queue_size": 3,
            "api_calls": 156,
            "watchers": [
                {"name": "Gmail", "status": "active", "events_detected": 12, "errors": 0},
                {"name": "WhatsApp", "status": "active", "events_detected": 8, "errors": 0},
                {"name": "Calendar", "status": "active", "events_detected": 5, "errors": 0},
                {"name": "Slack", "status": "active", "events_detected": 15, "errors": 0},
                {"name": "Discord", "status": "inactive", "events_detected": 0, "errors": 0},
                {"name": "FileSystem", "status": "active", "events_detected": 7, "errors": 0},
                {"name": "Twitter", "status": "inactive", "events_detected": 0, "errors": 0},
                {"name": "LinkedIn", "status": "inactive", "events_detected": 0, "errors": 0}
            ]
        }
    }

    with open(DATA_PATHS["logs"] / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print("✓ Created system statistics")
    return stats


def update_dashboard():
    """Update the Dashboard.md with actual data."""
    dashboard_path = NERVE_CENTER / "Dashboard.md"

    if not dashboard_path.exists():
        print("⚠ Dashboard.md not found, skipping update")
        return

    # Read current dashboard
    with open(dashboard_path, "r") as f:
        content = f.read()

    # Replace placeholders
    now = datetime.now()
    content = content.replace("{{timestamp}}", now.strftime("%Y-%m-%d %H:%M:%S"))
    content = content.replace("{{date}}", now.strftime("%A, %B %d, %Y"))

    # Write updated dashboard
    with open(dashboard_path, "w") as f:
        f.write(content)

    print("✓ Updated Dashboard.md with current timestamp")


def main():
    """Run all test data creation."""
    print("\n" + "="*60)
    print("   AI Employee - Test Data Generator")
    print("="*60 + "\n")

    print("Creating test data...\n")

    create_test_contacts()
    create_test_invoices()
    create_test_expenses()
    create_test_projects()
    create_test_events()
    create_test_activity_log()
    create_test_stats()
    update_dashboard()

    print("\n" + "="*60)
    print("   Test Data Created Successfully!")
    print("="*60)
    print("\nNext steps:")
    print("1. Open Obsidian and navigate to nerve_center/")
    print("2. Open Dashboard.md to see the multi-tab dashboard")
    print("3. Check nerve_center/inbox/ for sample events")
    print("4. Review the data in crm/, finances/, projects/ folders")
    print("\nTo start the orchestrator:")
    print("   python src/orchestrator.py")
    print("")


if __name__ == "__main__":
    main()
