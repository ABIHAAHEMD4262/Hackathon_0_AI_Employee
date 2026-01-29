"""
AI Employee - Master Startup Script
Runs all components of the AI Employee system
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from dotenv import load_dotenv


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     █████╗ ██╗    ███████╗███╗   ███╗██████╗ ██╗      ██████╗║
║    ██╔══██╗██║    ██╔════╝████╗ ████║██╔══██╗██║     ██╔═══██║
║    ███████║██║    █████╗  ██╔████╔██║██████╔╝██║     ██║   ██║
║    ██╔══██║██║    ██╔══╝  ██║╚██╔╝██║██╔═══╝ ██║     ██║   ██║
║    ██║  ██║██║    ███████╗██║ ╚═╝ ██║██║     ███████╗╚██████╔║
║    ╚═╝  ╚═╝╚═╝    ╚══════╝╚═╝     ╚═╝╚═╝     ╚══════╝ ╚═════╝║
║                                                              ║
║              Your Autonomous Business Assistant              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


def run_component(name: str, command: list, cwd: str):
    """Run a component in a subprocess"""
    print(f"[STARTING] {name}...")
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Stream output with prefix
        for line in process.stdout:
            print(f"[{name}] {line.rstrip()}")

    except Exception as e:
        print(f"[ERROR] {name} failed: {e}")


def main():
    load_dotenv()

    vault_path = Path(__file__).parent
    watchers_path = vault_path / 'watchers'
    dashboard_path = vault_path / 'dashboard'

    print_banner()

    print("Configuration:")
    print(f"  Vault Path: {vault_path}")
    print(f"  Email: {os.getenv('EMAIL_USER', 'Not configured')}")
    print()

    # Check if running specific component
    if len(sys.argv) > 1:
        component = sys.argv[1].lower()

        if component == 'gmail':
            print("Starting Gmail Watcher only...")
            os.chdir(watchers_path)
            os.system(f"python gmail_watcher_simple.py")

        elif component == 'executor':
            print("Starting Approval Executor only...")
            os.chdir(watchers_path)
            os.system(f"python approval_executor.py")

        elif component == 'dashboard':
            print("Starting Dashboard only...")
            os.chdir(dashboard_path)
            os.system("npm run dev")

        elif component == 'test':
            print("Running test mode (single check)...")
            os.chdir(watchers_path)
            os.system("python gmail_watcher_simple.py --test")
            os.system("python approval_executor.py --test")

        else:
            print(f"Unknown component: {component}")
            print("Available: gmail, executor, dashboard, test")
            sys.exit(1)

        return

    # Run all components
    print("Starting all components...")
    print("=" * 60)
    print()

    threads = []

    # Gmail Watcher
    t1 = threading.Thread(
        target=run_component,
        args=("Gmail", ["python", "gmail_watcher_simple.py"], str(watchers_path)),
        daemon=True
    )
    threads.append(t1)

    # Approval Executor
    t2 = threading.Thread(
        target=run_component,
        args=("Executor", ["python", "approval_executor.py"], str(watchers_path)),
        daemon=True
    )
    threads.append(t2)

    # Start all threads
    for t in threads:
        t.start()
        time.sleep(1)

    print()
    print("=" * 60)
    print("[READY] AI Employee is running!")
    print()
    print("Components:")
    print("  ✓ Gmail Watcher - Monitoring inbox every 2 minutes")
    print("  ✓ Approval Executor - Processing approved items every 10 seconds")
    print()
    print("To start the Dashboard, run in a new terminal:")
    print(f"  cd {dashboard_path}")
    print("  npm run dev")
    print()
    print("Dashboard will be at: http://localhost:3001")
    print()
    print("Press Ctrl+C to stop all components")
    print("=" * 60)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Stopping AI Employee...")
        print("Goodbye!")


if __name__ == '__main__':
    main()
