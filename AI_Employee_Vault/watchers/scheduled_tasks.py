"""
Scheduled Tasks Runner - Silver Tier Component
================================================
Runs scheduled tasks using APScheduler or cron-like scheduling.

This script handles:
1. Daily CEO Briefing (Monday 7:00 AM)
2. Email check every 5 minutes
3. Social media posting schedule
4. Weekly analytics reports
5. System health checks

Run with: python scheduled_tasks.py <vault_path>
Or add to cron: */5 * * * * python scheduled_tasks.py <vault_path> --check

CRON SETUP (Linux/Mac):
-----------------------
# Edit crontab: crontab -e
# Add these lines:

# Check emails every 5 minutes
*/5 * * * * cd /path/to/AI_Employee && python AI_Employee_Vault/watchers/scheduled_tasks.py AI_Employee_Vault --task email_check

# Generate CEO briefing every Monday at 7 AM
0 7 * * 1 cd /path/to/AI_Employee && python AI_Employee_Vault/watchers/scheduled_tasks.py AI_Employee_Vault --task ceo_briefing

# System health check every hour
0 * * * * cd /path/to/AI_Employee && python AI_Employee_Vault/watchers/scheduled_tasks.py AI_Employee_Vault --task health_check

WINDOWS TASK SCHEDULER:
-----------------------
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily/weekly/etc)
4. Action: Start a program
5. Program: python
6. Arguments: AI_Employee_Vault/watchers/scheduled_tasks.py AI_Employee_Vault --task <task_name>
"""

import time
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Callable, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ScheduledTasks')


class ScheduledTask:
    """Represents a scheduled task."""

    def __init__(self, name: str, func: Callable, schedule: str, description: str = ""):
        self.name = name
        self.func = func
        self.schedule = schedule  # cron-like string or keywords
        self.description = description
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.last_result = None


class ScheduledTasksRunner:
    """
    Manages and runs scheduled tasks for the AI Employee.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.tasks: Dict[str, ScheduledTask] = {}
        self.logs_folder = self.vault_path / 'Logs' / 'Scheduled'
        self.logs_folder.mkdir(parents=True, exist_ok=True)

        # State file to track last runs
        self.state_file = self.vault_path / '.scheduler_state.json'
        self._load_state()

        # Register default tasks
        self._register_default_tasks()

        logger.info(f"Scheduled Tasks Runner initialized for: {vault_path}")

    def _load_state(self):
        """Load scheduler state from file."""
        self.state = {}
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            except:
                pass

    def _save_state(self):
        """Save scheduler state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _register_default_tasks(self):
        """Register all default scheduled tasks."""

        # CEO Briefing - Every Monday at 7 AM
        self.register_task(
            name='ceo_briefing',
            func=self._task_ceo_briefing,
            schedule='weekly_monday_7am',
            description='Generate weekly CEO briefing'
        )

        # Email Check - Every 5 minutes
        self.register_task(
            name='email_check',
            func=self._task_email_check,
            schedule='every_5_minutes',
            description='Check for new emails'
        )

        # Health Check - Every hour
        self.register_task(
            name='health_check',
            func=self._task_health_check,
            schedule='hourly',
            description='System health check'
        )

        # Process Approvals - Every 10 minutes
        self.register_task(
            name='process_approvals',
            func=self._task_process_approvals,
            schedule='every_10_minutes',
            description='Process approved items'
        )

        # Daily Summary - Every day at 6 PM
        self.register_task(
            name='daily_summary',
            func=self._task_daily_summary,
            schedule='daily_6pm',
            description='Generate daily summary'
        )

        # Social Media Post - Optimal times
        self.register_task(
            name='social_check',
            func=self._task_social_check,
            schedule='every_hour',
            description='Check social media queue'
        )

    def register_task(self, name: str, func: Callable, schedule: str, description: str = ""):
        """Register a new scheduled task."""
        self.tasks[name] = ScheduledTask(name, func, schedule, description)
        logger.info(f"Registered task: {name} ({schedule})")

    def should_run(self, task_name: str) -> bool:
        """Check if a task should run based on its schedule."""
        if task_name not in self.tasks:
            return False

        task = self.tasks[task_name]
        last_run = self.state.get(f'{task_name}_last_run')

        if last_run:
            last_run_dt = datetime.fromisoformat(last_run)
        else:
            last_run_dt = datetime.min

        now = datetime.now()
        schedule = task.schedule

        # Parse schedule
        if schedule == 'every_5_minutes':
            return (now - last_run_dt).total_seconds() >= 300
        elif schedule == 'every_10_minutes':
            return (now - last_run_dt).total_seconds() >= 600
        elif schedule == 'hourly' or schedule == 'every_hour':
            return (now - last_run_dt).total_seconds() >= 3600
        elif schedule == 'daily_6pm':
            if now.hour == 18 and (now - last_run_dt).total_seconds() >= 82800:  # 23 hours
                return True
        elif schedule == 'weekly_monday_7am':
            if now.weekday() == 0 and now.hour == 7:
                if (now - last_run_dt).days >= 6:  # At least 6 days since last run
                    return True

        return False

    def run_task(self, task_name: str, force: bool = False) -> Dict[str, Any]:
        """Run a specific task."""
        if task_name not in self.tasks:
            return {"success": False, "error": f"Unknown task: {task_name}"}

        task = self.tasks[task_name]

        if not force and not self.should_run(task_name):
            return {"success": False, "message": "Not scheduled to run yet"}

        logger.info(f"Running task: {task_name}")
        start_time = datetime.now()

        try:
            result = task.func()

            # Update state
            self.state[f'{task_name}_last_run'] = start_time.isoformat()
            self.state[f'{task_name}_last_result'] = 'success'
            self._save_state()

            # Log the run
            self._log_task_run(task_name, 'success', result, start_time)

            return {
                "success": True,
                "task": task_name,
                "result": result,
                "duration": (datetime.now() - start_time).total_seconds()
            }

        except Exception as e:
            logger.error(f"Task {task_name} failed: {e}")

            self.state[f'{task_name}_last_result'] = f'error: {str(e)}'
            self._save_state()

            self._log_task_run(task_name, 'error', str(e), start_time)

            return {
                "success": False,
                "task": task_name,
                "error": str(e)
            }

    def run_all_due(self) -> List[Dict[str, Any]]:
        """Run all tasks that are due."""
        results = []
        for task_name in self.tasks:
            if self.should_run(task_name):
                result = self.run_task(task_name)
                results.append(result)
        return results

    def _log_task_run(self, task_name: str, status: str, result: Any, start_time: datetime):
        """Log a task run to file."""
        log_file = self.logs_folder / f'scheduled_{datetime.now().strftime("%Y%m%d")}.md'

        with open(log_file, 'a') as f:
            f.write(f"\n## {start_time.strftime('%H:%M:%S')} - {task_name}\n")
            f.write(f"- **Status:** {status}\n")
            f.write(f"- **Result:** {str(result)[:200]}\n")
            f.write("\n")

    # ==================== TASK IMPLEMENTATIONS ====================

    def _task_ceo_briefing(self) -> Dict[str, Any]:
        """Generate weekly CEO briefing."""
        from ceo_briefing import CEOBriefingGenerator

        generator = CEOBriefingGenerator(str(self.vault_path))
        briefing_path = generator.generate_weekly_briefing()

        return {
            "briefing_path": str(briefing_path),
            "message": "CEO Briefing generated successfully"
        }

    def _task_email_check(self) -> Dict[str, Any]:
        """Check for new emails."""
        # This would call the Gmail watcher
        # For now, just check the needs_action folder

        needs_action = self.vault_path / 'Needs_Action' / 'Emails'
        email_count = len(list(needs_action.glob('*.md'))) if needs_action.exists() else 0

        return {
            "emails_pending": email_count,
            "message": f"{email_count} emails pending action"
        }

    def _task_health_check(self) -> Dict[str, Any]:
        """System health check."""
        health = {
            "vault_accessible": self.vault_path.exists(),
            "folders_exist": {},
            "errors_today": 0
        }

        # Check key folders
        for folder in ['Needs_Action', 'Approved', 'Done', 'Logs']:
            folder_path = self.vault_path / folder
            health["folders_exist"][folder] = folder_path.exists()

        # Count errors today
        error_log = self.vault_path / 'Logs' / 'Errors' / f'errors_{datetime.now().strftime("%Y%m%d")}.json'
        if error_log.exists():
            try:
                with open(error_log, 'r') as f:
                    errors = json.load(f)
                    health["errors_today"] = len(errors)
            except:
                pass

        return health

    def _task_process_approvals(self) -> Dict[str, Any]:
        """Process approved items."""
        approved_folder = self.vault_path / 'Approved'
        processed = 0

        if approved_folder.exists():
            for item in approved_folder.glob('*.md'):
                # Move to done after processing
                # In production, this would trigger the actual action
                processed += 1

        return {
            "processed": processed,
            "message": f"Processed {processed} approved items"
        }

    def _task_daily_summary(self) -> Dict[str, Any]:
        """Generate daily summary."""
        summary = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "tasks_completed": 0,
            "tasks_pending": 0,
            "emails_handled": 0
        }

        # Count items in folders
        done_folder = self.vault_path / 'Done'
        if done_folder.exists():
            today = datetime.now().date()
            for item in done_folder.glob('*.md'):
                if datetime.fromtimestamp(item.stat().st_mtime).date() == today:
                    summary["tasks_completed"] += 1

        needs_action = self.vault_path / 'Needs_Action'
        if needs_action.exists():
            summary["tasks_pending"] = len(list(needs_action.rglob('*.md')))

        return summary

    def _task_social_check(self) -> Dict[str, Any]:
        """Check social media queue."""
        queue_folder = self.vault_path / 'Marketing' / 'Social_Queue'
        posts_pending = len(list(queue_folder.glob('*.md'))) if queue_folder.exists() else 0

        return {
            "posts_pending": posts_pending,
            "message": f"{posts_pending} social posts in queue"
        }


def main():
    """Main entry point for scheduled tasks."""
    parser = argparse.ArgumentParser(description='AI Employee Scheduled Tasks Runner')
    parser.add_argument('vault_path', help='Path to the vault')
    parser.add_argument('--task', help='Run a specific task')
    parser.add_argument('--force', action='store_true', help='Force run even if not scheduled')
    parser.add_argument('--list', action='store_true', help='List all tasks')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon checking all tasks')

    args = parser.parse_args()

    runner = ScheduledTasksRunner(args.vault_path)

    if args.list:
        print("Registered Tasks:")
        print("=" * 50)
        for name, task in runner.tasks.items():
            print(f"  {name}: {task.description} ({task.schedule})")
        return

    if args.task:
        result = runner.run_task(args.task, force=args.force)
        print(json.dumps(result, indent=2))
        return

    if args.daemon:
        print("Starting Scheduled Tasks Daemon")
        print("=" * 50)
        print(f"Vault: {args.vault_path}")
        print("Press Ctrl+C to stop")
        print("=" * 50)

        while True:
            try:
                results = runner.run_all_due()
                for result in results:
                    if result.get('success'):
                        logger.info(f"Completed: {result['task']}")
                    else:
                        logger.warning(f"Failed: {result['task']} - {result.get('error')}")
            except KeyboardInterrupt:
                print("\nDaemon stopped")
                break
            except Exception as e:
                logger.error(f"Daemon error: {e}")

            time.sleep(60)  # Check every minute
        return

    # Default: check and run all due tasks
    results = runner.run_all_due()
    if results:
        for result in results:
            print(f"Task: {result.get('task', 'unknown')} - {'Success' if result.get('success') else 'Failed'}")
    else:
        print("No tasks due to run")


if __name__ == '__main__':
    main()
