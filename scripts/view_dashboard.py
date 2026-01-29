#!/usr/bin/env python3
"""
AI Employee Dashboard Viewer
============================
A terminal-based dashboard viewer to see your AI Employee status.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Try to import rich for pretty output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Paths
NERVE_CENTER = Path(__file__).parent.parent / "nerve_center"


def load_json(filepath):
    """Load JSON file safely."""
    try:
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        pass
    return []


def print_simple_dashboard():
    """Print a simple text dashboard without rich."""
    print("\n" + "=" * 70)
    print("                    AI EMPLOYEE DASHBOARD")
    print("=" * 70)
    print(f"  Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Contacts
    contacts = load_json(NERVE_CENTER / "crm" / "contacts.json")
    print(f"\n📧 CONTACTS: {len(contacts)} total")
    for c in contacts[:3]:
        status = "⭐ VIP" if c.get("is_vip") else ""
        print(f"   • {c['name']} ({c['email']}) - {c['type']} {status}")

    # Invoices
    invoices = load_json(NERVE_CENTER / "finances" / "invoices.json")
    sent = [i for i in invoices if i['type'] == 'sent']
    received = [i for i in invoices if i['type'] == 'received']
    print(f"\n💰 INVOICES: {len(sent)} sent, {len(received)} received")

    total_ar = sum(
        sum(item['quantity'] * item['unit_price'] for item in i.get('line_items', []))
        for i in sent if i['status'] != 'paid'
    )
    print(f"   Outstanding Receivables: ${total_ar:,.2f}")

    # Projects & Tasks
    projects = load_json(NERVE_CENTER / "projects" / "projects.json")
    tasks = load_json(NERVE_CENTER / "projects" / "tasks.json")
    active_projects = [p for p in projects if p['status'] == 'active']

    todo = len([t for t in tasks if t['status'] == 'todo'])
    in_progress = len([t for t in tasks if t['status'] == 'in_progress'])
    completed = len([t for t in tasks if t['status'] == 'completed'])
    blocked = len([t for t in tasks if t['status'] == 'blocked'])
    overdue = len([t for t in tasks if t.get('due_date') and t['status'] != 'completed'
                   and datetime.fromisoformat(t['due_date']) < datetime.now()])

    print(f"\n✅ TASKS: {len(tasks)} total")
    print(f"   📋 To Do: {todo} | 🔄 In Progress: {in_progress} | ✓ Done: {completed}")
    print(f"   🚫 Blocked: {blocked} | ⏰ Overdue: {overdue}")

    print(f"\n📁 ACTIVE PROJECTS: {len(active_projects)}")
    for p in active_projects:
        budget_pct = (p.get('budget_spent', 0) / p['budget'] * 100) if p.get('budget', 0) > 0 else 0
        print(f"   • {p['name']} - {p['client']} (Budget: {budget_pct:.0f}% used)")

    # Inbox Events
    inbox = NERVE_CENTER / "inbox"
    events = list(inbox.glob("*.json")) if inbox.exists() else []
    print(f"\n📥 INBOX: {len(events)} pending events")
    for evt_file in events[:3]:
        try:
            evt = json.load(open(evt_file))
            print(f"   • [{evt['type']}] {evt.get('data', {}).get('subject', evt.get('data', {}).get('body', '')[:40])}")
        except:
            pass

    # System Status
    stats = load_json(NERVE_CENTER / "logs" / "stats.json")
    if stats:
        latest = list(stats.values())[-1]
        print(f"\n⚙️  SYSTEM STATUS")
        print(f"   Events Processed: {latest.get('events_processed', 0)}")
        print(f"   API Calls: {latest.get('api_calls', 0)}")
        print(f"   Watchers Active: {len([w for w in latest.get('watchers', []) if w['status'] == 'active'])}")

    print("\n" + "=" * 70)
    print("  View full dashboard: Open nerve_center/Dashboard.md in Obsidian")
    print("=" * 70 + "\n")


def print_rich_dashboard():
    """Print a rich formatted dashboard."""
    console = Console()

    # Header
    console.print(Panel.fit(
        "[bold blue]AI EMPLOYEE DASHBOARD[/bold blue]\n" +
        f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        border_style="blue"
    ))

    # Load data
    contacts = load_json(NERVE_CENTER / "crm" / "contacts.json")
    invoices = load_json(NERVE_CENTER / "finances" / "invoices.json")
    expenses = load_json(NERVE_CENTER / "finances" / "expenses.json")
    projects = load_json(NERVE_CENTER / "projects" / "projects.json")
    tasks = load_json(NERVE_CENTER / "projects" / "tasks.json")

    # === CONTACTS TABLE ===
    contacts_table = Table(title="👥 Contacts (CRM)", box=box.ROUNDED)
    contacts_table.add_column("Name", style="cyan")
    contacts_table.add_column("Company", style="white")
    contacts_table.add_column("Type", style="green")
    contacts_table.add_column("Status", style="yellow")
    contacts_table.add_column("VIP", style="red")

    for c in contacts[:5]:
        vip = "⭐" if c.get("is_vip") else ""
        contacts_table.add_row(
            c['name'],
            c.get('company', ''),
            c['type'],
            c['status'],
            vip
        )
    console.print(contacts_table)

    # === FINANCIAL TABLE ===
    fin_table = Table(title="💰 Financial Overview", box=box.ROUNDED)
    fin_table.add_column("Metric", style="cyan")
    fin_table.add_column("Amount", style="green", justify="right")

    sent_invoices = [i for i in invoices if i['type'] == 'sent']
    received_invoices = [i for i in invoices if i['type'] == 'received']

    def calc_total(inv):
        return sum(
            item['quantity'] * item['unit_price']
            for item in inv.get('line_items', [])
        ) - inv.get('discount', 0)

    outstanding_ar = sum(calc_total(i) for i in sent_invoices if i['status'] not in ['paid', 'cancelled'])
    outstanding_ap = sum(calc_total(i) for i in received_invoices if i['status'] not in ['paid', 'cancelled'])
    total_expenses = sum(e['amount'] for e in expenses)

    fin_table.add_row("Invoices Sent", str(len(sent_invoices)))
    fin_table.add_row("Outstanding Receivables", f"${outstanding_ar:,.2f}")
    fin_table.add_row("Bills Pending", f"${outstanding_ap:,.2f}")
    fin_table.add_row("Expenses This Month", f"${total_expenses:,.2f}")
    console.print(fin_table)

    # === TASKS TABLE ===
    tasks_table = Table(title="✅ Tasks Overview", box=box.ROUNDED)
    tasks_table.add_column("Status", style="cyan")
    tasks_table.add_column("Count", justify="right", style="white")
    tasks_table.add_column("Visual", style="green")

    status_counts = {
        "todo": len([t for t in tasks if t['status'] == 'todo']),
        "in_progress": len([t for t in tasks if t['status'] == 'in_progress']),
        "completed": len([t for t in tasks if t['status'] == 'completed']),
        "blocked": len([t for t in tasks if t['status'] == 'blocked']),
    }

    status_colors = {
        "todo": "yellow",
        "in_progress": "blue",
        "completed": "green",
        "blocked": "red"
    }

    for status, count in status_counts.items():
        bar = "█" * min(count * 2, 20)
        tasks_table.add_row(
            status.replace("_", " ").title(),
            str(count),
            f"[{status_colors[status]}]{bar}[/{status_colors[status]}]"
        )
    console.print(tasks_table)

    # === PROJECTS TABLE ===
    proj_table = Table(title="📁 Active Projects", box=box.ROUNDED)
    proj_table.add_column("Project", style="cyan")
    proj_table.add_column("Client", style="white")
    proj_table.add_column("Budget", justify="right", style="green")
    proj_table.add_column("Progress", style="yellow")

    for p in projects:
        if p['status'] == 'active':
            budget = p.get('budget', 0)
            spent = p.get('budget_spent', 0)
            pct = int(spent / budget * 100) if budget > 0 else 0
            progress_bar = f"[{'green' if pct < 80 else 'red'}]{'█' * (pct // 10)}{'░' * (10 - pct // 10)}[/] {pct}%"
            proj_table.add_row(
                p['name'],
                p.get('client', ''),
                f"${spent:,.0f} / ${budget:,.0f}",
                progress_bar
            )
    console.print(proj_table)

    # === INBOX EVENTS ===
    inbox = NERVE_CENTER / "inbox"
    events = list(inbox.glob("*.json")) if inbox.exists() else []

    if events:
        inbox_table = Table(title="📥 Pending Inbox Events", box=box.ROUNDED)
        inbox_table.add_column("Type", style="cyan")
        inbox_table.add_column("Source", style="white")
        inbox_table.add_column("Preview", style="dim")

        for evt_file in events[:5]:
            try:
                evt = json.load(open(evt_file))
                preview = evt.get('data', {}).get('subject',
                          evt.get('data', {}).get('body',
                          evt.get('data', {}).get('filename', '')))[:50]
                inbox_table.add_row(
                    evt['type'].replace('_', ' ').title(),
                    evt['source'],
                    preview
                )
            except:
                pass
        console.print(inbox_table)

    # === SYSTEM STATUS ===
    stats = load_json(NERVE_CENTER / "logs" / "stats.json")
    if stats:
        latest = list(stats.values())[-1]

        sys_table = Table(title="⚙️ System Status", box=box.ROUNDED)
        sys_table.add_column("Watcher", style="cyan")
        sys_table.add_column("Status", style="white")
        sys_table.add_column("Events", justify="right", style="green")
        sys_table.add_column("Errors", justify="right", style="red")

        for w in latest.get('watchers', []):
            status = w.get('status', 'unknown')
            status_icon = "🟢" if status == 'active' else "🟡"
            sys_table.add_row(
                w.get('name', 'Unknown'),
                f"{status_icon} {status}",
                str(w.get('events_detected', 0)),
                str(w.get('errors', 0))
            )
        console.print(sys_table)

    console.print("\n[dim]View full dashboard: Open nerve_center/Dashboard.md in Obsidian[/dim]\n")


def main():
    """Main entry point."""
    if RICH_AVAILABLE:
        print_rich_dashboard()
    else:
        print_simple_dashboard()


if __name__ == "__main__":
    main()
