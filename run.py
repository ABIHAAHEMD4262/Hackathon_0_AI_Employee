#!/usr/bin/env python3
"""
AI Employee - Main Entry Point
================================
Start your AI Employee with one command.

Usage:
    python run.py                   # Run full system
    python run.py --dashboard       # Start dashboard only
    python run.py --orchestrator    # Start orchestrator only
    python run.py --scheduler       # Start scheduled tasks daemon
    python run.py --demo            # Create demo tasks and run
    python run.py --status          # Check system status

Author: Syeda Abiha Ahmed
Project: Personal AI Employee Hackathon
"""

import os
import sys
import json
import argparse
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent
VAULT_PATH = PROJECT_ROOT / 'AI_Employee_Vault'
CONFIG_PATH = PROJECT_ROOT / 'config'
DASHBOARD_PATH = VAULT_PATH / 'dashboard'


def print_banner():
    """Print ASCII art banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║      🤖 AI EMPLOYEE - Your Personal Digital FTE 🤖           ║
    ║                                                               ║
    ║   "Your life and business on autopilot"                       ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_environment():
    """Check if environment is properly set up."""
    issues = []

    # Check Python version
    if sys.version_info < (3, 10):
        issues.append(f"Python 3.10+ required (current: {sys.version_info.major}.{sys.version_info.minor})")

    # Check vault exists
    if not VAULT_PATH.exists():
        issues.append(f"Vault not found: {VAULT_PATH}")

    # Check credentials file
    env_file = CONFIG_PATH / 'credentials' / '.env'
    if not env_file.exists():
        issues.append("Credentials file not found. Create config/credentials/.env")

    # Check Node.js for dashboard
    try:
        subprocess.run(['node', '--version'], capture_output=True, check=True)
    except:
        issues.append("Node.js not found. Required for dashboard.")

    return issues


def load_env():
    """Load environment variables from .env file."""
    env_file = CONFIG_PATH / 'credentials' / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def start_dashboard():
    """Start the Next.js dashboard."""
    print("\n📊 Starting Dashboard...")
    print(f"   Directory: {DASHBOARD_PATH}")

    os.chdir(DASHBOARD_PATH)

    # Check if node_modules exists
    if not (DASHBOARD_PATH / 'node_modules').exists():
        print("   Installing dependencies...")
        subprocess.run(['npm', 'install'], check=True)

    print("   Starting Next.js server...")
    print("   Dashboard will be available at: http://localhost:3000")
    print("\n   Press Ctrl+C to stop\n")

    # Open browser after a delay
    webbrowser.open('http://localhost:3000')

    subprocess.run(['npm', 'run', 'dev'])


def start_orchestrator():
    """Start the AI Employee orchestrator."""
    print("\n⚡ Starting Orchestrator...")
    print(f"   Vault: {VAULT_PATH}")

    sys.path.insert(0, str(VAULT_PATH / 'watchers'))
    from orchestrator import AIEmployeeOrchestrator

    orchestrator = AIEmployeeOrchestrator(str(VAULT_PATH))
    orchestrator.run()


def start_scheduler():
    """Start the scheduled tasks daemon."""
    print("\n📅 Starting Scheduled Tasks Daemon...")
    print(f"   Vault: {VAULT_PATH}")

    sys.path.insert(0, str(VAULT_PATH / 'watchers'))
    from scheduled_tasks import ScheduledTasksRunner

    runner = ScheduledTasksRunner(str(VAULT_PATH))

    print("\n   Registered Tasks:")
    for name, task in runner.tasks.items():
        print(f"   - {name}: {task.description}")

    print("\n   Press Ctrl+C to stop\n")

    import time
    while True:
        try:
            results = runner.run_all_due()
            for result in results:
                status = "✅" if result.get('success') else "❌"
                print(f"   {status} {result.get('task', 'unknown')}")
        except KeyboardInterrupt:
            print("\n   Scheduler stopped")
            break
        time.sleep(60)


def check_status():
    """Check system status."""
    print("\n📊 System Status")
    print("=" * 50)

    # Check folders
    folders = ['Needs_Action', 'In_Progress', 'Pending_Approval', 'Approved', 'Done', 'Logs']
    print("\n📁 Folder Status:")
    for folder in folders:
        folder_path = VAULT_PATH / folder
        if folder_path.exists():
            count = len(list(folder_path.rglob('*.md')))
            print(f"   ✅ {folder}: {count} files")
        else:
            print(f"   ❌ {folder}: Not found")

    # Check watchers
    print("\n🔍 Watcher Scripts:")
    watchers = ['gmail_watcher.py', 'linkedin_watcher.py', 'whatsapp_watcher.py']
    for watcher in watchers:
        watcher_path = VAULT_PATH / 'watchers' / watcher
        if watcher_path.exists():
            print(f"   ✅ {watcher}")
        else:
            print(f"   ❌ {watcher}")

    # Check MCP servers
    print("\n🔌 MCP Servers:")
    servers = ['email_server.py', 'social_media_server.py']
    for server in servers:
        server_path = VAULT_PATH / 'mcp_servers' / server
        if server_path.exists():
            print(f"   ✅ {server}")
        else:
            print(f"   ❌ {server}")

    # Check skills
    print("\n🎯 Agent Skills:")
    skills_path = VAULT_PATH / '.claude' / 'skills'
    if skills_path.exists():
        skills = list(skills_path.glob('*.md'))
        print(f"   ✅ {len(skills)} skills defined")
        for skill in skills:
            print(f"      - {skill.stem}")
    else:
        print("   ❌ No skills found")

    # Check credentials
    print("\n🔑 Credentials:")
    env_file = CONFIG_PATH / 'credentials' / '.env'
    if env_file.exists():
        print("   ✅ .env file exists")
    else:
        print("   ❌ .env file not found")

    print("\n" + "=" * 50)


def create_demo():
    """Create demo tasks to test the system."""
    print("\n🎮 Creating Demo Tasks...")

    # Create sample email task
    emails_folder = VAULT_PATH / 'Needs_Action' / 'Emails'
    emails_folder.mkdir(parents=True, exist_ok=True)

    demo_email = emails_folder / 'DEMO_EMAIL_001.md'
    demo_email.write_text(f'''---
type: email
from: client@example.com
subject: Project Inquiry
received: {datetime.now().isoformat()}
priority: high
status: pending
---

# Demo Email - Project Inquiry

## From
**client@example.com**

## Subject
Interested in AI Automation Services

## Content

Hello,

I found your profile and I'm interested in your AI automation services.

We're looking for:
1. Email automation
2. Social media scheduling
3. Task management system

Can you provide a quote?

Best regards,
Demo Client

---

## Suggested Actions
- [ ] Reply with service offerings
- [ ] Schedule discovery call
- [ ] Add to CRM
''')

    print(f"   ✅ Created: {demo_email}")

    # Create sample LinkedIn notification
    linkedin_folder = VAULT_PATH / 'Needs_Action' / 'LinkedIn'
    linkedin_folder.mkdir(parents=True, exist_ok=True)

    demo_linkedin = linkedin_folder / 'DEMO_LINKEDIN_001.md'
    demo_linkedin.write_text(f'''---
type: linkedin_notification
notification_type: connection_request
received: {datetime.now().isoformat()}
priority: medium
status: pending
---

# Demo LinkedIn - Connection Request

## Notification
New connection request from **John Smith, CEO at Tech Startup**

## Profile Summary
- Position: CEO
- Company: Tech Startup
- Location: San Francisco, CA
- Connections: 500+

## Suggested Actions
- [ ] Accept connection
- [ ] Send welcome message
- [ ] Add to networking list
''')

    print(f"   ✅ Created: {demo_linkedin}")

    print("\n   Demo tasks created! Run the orchestrator to process them.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI Employee - Your Personal Digital FTE',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run.py                 # Run full system (dashboard + orchestrator)
  python run.py --dashboard     # Start dashboard only
  python run.py --orchestrator  # Start orchestrator only
  python run.py --scheduler     # Start scheduled tasks daemon
  python run.py --status        # Check system status
  python run.py --demo          # Create demo tasks
        '''
    )

    parser.add_argument('--dashboard', action='store_true', help='Start dashboard only')
    parser.add_argument('--orchestrator', action='store_true', help='Start orchestrator only')
    parser.add_argument('--scheduler', action='store_true', help='Start scheduled tasks daemon')
    parser.add_argument('--status', action='store_true', help='Check system status')
    parser.add_argument('--demo', action='store_true', help='Create demo tasks')
    parser.add_argument('--no-banner', action='store_true', help='Skip banner')

    args = parser.parse_args()

    if not args.no_banner:
        print_banner()

    # Check environment
    issues = check_environment()
    if issues:
        print("\n⚠️  Environment Issues:")
        for issue in issues:
            print(f"   - {issue}")
        if args.status:
            print()
        elif not args.demo:
            print("\n   Please fix these issues before continuing.")
            return 1

    # Load environment variables
    load_env()

    # Handle commands
    if args.status:
        check_status()
        return 0

    if args.demo:
        create_demo()
        return 0

    if args.dashboard:
        start_dashboard()
        return 0

    if args.orchestrator:
        start_orchestrator()
        return 0

    if args.scheduler:
        start_scheduler()
        return 0

    # Default: Show status and provide options
    check_status()

    print("\n🚀 Quick Start Options:")
    print("   1. python run.py --dashboard     # Start web dashboard")
    print("   2. python run.py --orchestrator  # Start AI processing")
    print("   3. python run.py --scheduler     # Start scheduled tasks")
    print("   4. python run.py --demo          # Create demo tasks")

    return 0


if __name__ == '__main__':
    sys.exit(main())
