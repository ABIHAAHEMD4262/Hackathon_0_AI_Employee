"""
AI Employee Scheduler
Handles scheduled tasks and cron-like operations
"""

import os
import sys
import time
import json
import subprocess
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Callable
from dotenv import load_dotenv

load_dotenv()


class TaskScheduler:
    """
    Scheduler for AI Employee automated tasks
    Can be run as a daemon or triggered via cron/Task Scheduler
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_path = self.vault_path / 'Logs'
        self.tasks_path = self.vault_path / 'Tasks'
        self.watchers_path = self.vault_path / 'watchers'

        # Create directories
        self.logs_path.mkdir(exist_ok=True)
        self.tasks_path.mkdir(exist_ok=True)

        # Schedule configuration
        self.schedule_file = self.vault_path / '.schedule.json'
        self.schedule = self._load_schedule()

        # Track last run times
        self.last_run_file = self.vault_path / '.last_run.json'
        self.last_run = self._load_last_run()

        self.log("Scheduler initialized")

    def _load_schedule(self) -> Dict:
        """Load schedule configuration"""
        if self.schedule_file.exists():
            return json.loads(self.schedule_file.read_text())

        # Default schedule
        default_schedule = {
            "tasks": [
                {
                    "name": "gmail_check",
                    "description": "Check Gmail for new emails",
                    "command": "python watchers/gmail_watcher_simple.py --test",
                    "interval_minutes": 2,
                    "enabled": True
                },
                {
                    "name": "approval_executor",
                    "description": "Process approved items",
                    "command": "python watchers/approval_executor.py --test",
                    "interval_minutes": 1,
                    "enabled": True
                },
                {
                    "name": "ceo_briefing",
                    "description": "Generate weekly CEO briefing",
                    "command": "python watchers/ceo_briefing.py --generate",
                    "cron": "0 7 * * 1",  # Every Monday at 7 AM
                    "enabled": True
                },
                {
                    "name": "daily_summary",
                    "description": "Generate daily activity summary",
                    "command": "python watchers/ceo_briefing.py --daily",
                    "cron": "0 18 * * *",  # Every day at 6 PM
                    "enabled": True
                },
                {
                    "name": "whatsapp_check",
                    "description": "Check WhatsApp for messages",
                    "command": "python watchers/whatsapp_watcher.py --test",
                    "interval_minutes": 5,
                    "enabled": False  # Requires browser, disable by default
                }
            ]
        }

        self.schedule_file.write_text(json.dumps(default_schedule, indent=2))
        return default_schedule

    def _load_last_run(self) -> Dict:
        """Load last run times"""
        if self.last_run_file.exists():
            try:
                return json.loads(self.last_run_file.read_text())
            except:
                return {}
        return {}

    def _save_last_run(self):
        """Save last run times"""
        self.last_run_file.write_text(json.dumps(self.last_run, indent=2))

    def log(self, message: str, level: str = 'INFO'):
        """Log message"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [Scheduler] [{level}] {message}"
        print(log_entry)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_path / f'scheduler_{today}.log'
        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')

    def parse_cron(self, cron_expr: str) -> bool:
        """
        Simple cron parser - checks if current time matches cron expression
        Format: minute hour day_of_month month day_of_week
        """
        parts = cron_expr.split()
        if len(parts) != 5:
            return False

        now = datetime.now()
        minute, hour, dom, month, dow = parts

        def matches(value: str, current: int) -> bool:
            if value == '*':
                return True
            if value.isdigit():
                return int(value) == current
            if '/' in value:
                _, interval = value.split('/')
                return current % int(interval) == 0
            return False

        return (
            matches(minute, now.minute) and
            matches(hour, now.hour) and
            matches(dom, now.day) and
            matches(month, now.month) and
            matches(dow, now.weekday())
        )

    def should_run_task(self, task: Dict) -> bool:
        """Check if a task should run now"""
        if not task.get('enabled', True):
            return False

        task_name = task['name']
        now = datetime.now()

        # Check interval-based tasks
        if 'interval_minutes' in task:
            last_run_str = self.last_run.get(task_name)
            if not last_run_str:
                return True

            last_run = datetime.fromisoformat(last_run_str)
            interval = timedelta(minutes=task['interval_minutes'])

            return now - last_run >= interval

        # Check cron-based tasks
        if 'cron' in task:
            # Only run cron tasks at the start of matching minute
            if now.second > 30:
                return False
            return self.parse_cron(task['cron'])

        return False

    def run_task(self, task: Dict) -> bool:
        """Execute a scheduled task"""
        task_name = task['name']
        command = task['command']

        self.log(f"Running task: {task_name}")

        try:
            # Run command from vault directory
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.vault_path),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Update last run time
            self.last_run[task_name] = datetime.now().isoformat()
            self._save_last_run()

            if result.returncode == 0:
                self.log(f"Task {task_name} completed successfully")
                return True
            else:
                self.log(f"Task {task_name} failed: {result.stderr}", 'ERROR')
                return False

        except subprocess.TimeoutExpired:
            self.log(f"Task {task_name} timed out", 'ERROR')
            return False
        except Exception as e:
            self.log(f"Task {task_name} error: {e}", 'ERROR')
            return False

    def run_once(self):
        """Run all due tasks once"""
        self.log("Checking scheduled tasks...")

        tasks_run = 0
        for task in self.schedule.get('tasks', []):
            if self.should_run_task(task):
                if self.run_task(task):
                    tasks_run += 1

        self.log(f"Completed {tasks_run} tasks")
        return tasks_run

    def run_continuous(self, check_interval: int = 30):
        """Run scheduler continuously"""
        self.log(f"Starting continuous scheduler (checking every {check_interval}s)")

        while True:
            try:
                self.run_once()
            except Exception as e:
                self.log(f"Scheduler error: {e}", 'ERROR')

            time.sleep(check_interval)

    def run_specific_task(self, task_name: str) -> bool:
        """Run a specific task by name"""
        for task in self.schedule.get('tasks', []):
            if task['name'] == task_name:
                return self.run_task(task)

        self.log(f"Task not found: {task_name}", 'ERROR')
        return False

    def list_tasks(self):
        """List all scheduled tasks"""
        print("\n" + "=" * 60)
        print("  SCHEDULED TASKS")
        print("=" * 60)

        for task in self.schedule.get('tasks', []):
            status = "✅ Enabled" if task.get('enabled', True) else "❌ Disabled"
            schedule = task.get('cron', f"Every {task.get('interval_minutes', '?')} min")

            last_run = self.last_run.get(task['name'], 'Never')
            if last_run != 'Never':
                last_run = datetime.fromisoformat(last_run).strftime('%Y-%m-%d %H:%M')

            print(f"\n{task['name']}")
            print(f"  Description: {task['description']}")
            print(f"  Schedule: {schedule}")
            print(f"  Status: {status}")
            print(f"  Last Run: {last_run}")

        print("\n" + "=" * 60)


def generate_cron_commands(vault_path: str):
    """Generate cron commands for Linux/Mac"""
    print("""
# Add these lines to your crontab (run: crontab -e)

# Check Gmail every 2 minutes
*/2 * * * * cd {vault} && source venv/bin/activate && python watchers/gmail_watcher_simple.py --test >> Logs/cron.log 2>&1

# Process approvals every minute
* * * * * cd {vault} && source venv/bin/activate && python watchers/approval_executor.py --test >> Logs/cron.log 2>&1

# CEO Briefing every Monday at 7 AM
0 7 * * 1 cd {vault} && source venv/bin/activate && python watchers/ceo_briefing.py --generate >> Logs/cron.log 2>&1

# Daily summary at 6 PM
0 18 * * * cd {vault} && source venv/bin/activate && python watchers/ceo_briefing.py --daily >> Logs/cron.log 2>&1

# Run full scheduler daemon (alternative to individual crons)
# @reboot cd {vault} && source venv/bin/activate && python scheduler.py --daemon >> Logs/scheduler.log 2>&1
""".format(vault=vault_path))


def generate_windows_tasks(vault_path: str):
    """Generate Windows Task Scheduler commands"""
    print("""
# Windows Task Scheduler Setup

# 1. Open Task Scheduler (taskschd.msc)
# 2. Create Basic Task for each:

# Gmail Check (Every 2 minutes)
# Action: Start a program
# Program: cmd
# Arguments: /c "cd /d {vault} && venv\\Scripts\\activate && python watchers\\gmail_watcher_simple.py --test"

# Approval Executor (Every 1 minute)
# Program: cmd
# Arguments: /c "cd /d {vault} && venv\\Scripts\\activate && python watchers\\approval_executor.py --test"

# CEO Briefing (Weekly, Monday 7 AM)
# Program: cmd
# Arguments: /c "cd /d {vault} && venv\\Scripts\\activate && python watchers\\ceo_briefing.py --generate"

# Or use the scheduler daemon:
# Program: cmd
# Arguments: /c "cd /d {vault} && venv\\Scripts\\activate && python scheduler.py --daemon"
""".format(vault=vault_path.replace('/', '\\')))


def main():
    """Main entry point"""
    vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent))

    print("=" * 50)
    print("  AI Employee Scheduler")
    print("=" * 50)
    print(f"Vault: {vault_path}")
    print()

    scheduler = TaskScheduler(vault_path)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == '--list':
            scheduler.list_tasks()

        elif cmd == '--once':
            scheduler.run_once()

        elif cmd == '--daemon':
            print("Starting scheduler daemon...")
            print("Press Ctrl+C to stop\n")
            try:
                scheduler.run_continuous()
            except KeyboardInterrupt:
                print("\n\nShutdown requested. Goodbye!")

        elif cmd == '--run':
            if len(sys.argv) > 2:
                task_name = sys.argv[2]
                scheduler.run_specific_task(task_name)
            else:
                print("Usage: scheduler.py --run <task_name>")

        elif cmd == '--cron':
            generate_cron_commands(vault_path)

        elif cmd == '--windows':
            generate_windows_tasks(vault_path)

        else:
            print(f"Unknown command: {cmd}")
            print("\nUsage:")
            print("  --list     List all scheduled tasks")
            print("  --once     Run all due tasks once")
            print("  --daemon   Run continuously")
            print("  --run NAME Run specific task")
            print("  --cron     Generate cron commands (Linux/Mac)")
            print("  --windows  Generate Windows Task Scheduler setup")

    else:
        print("Usage:")
        print("  python scheduler.py --list")
        print("  python scheduler.py --once")
        print("  python scheduler.py --daemon")
        print("  python scheduler.py --run <task_name>")
        print("  python scheduler.py --cron")
        print("  python scheduler.py --windows")


if __name__ == '__main__':
    main()
