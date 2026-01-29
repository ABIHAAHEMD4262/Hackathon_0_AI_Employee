"""
AI Employee Orchestrator - Silver Tier Component
=================================================
The "brain" that coordinates all watchers and creates Plan.md files.

This is the Claude Reasoning Loop:
1. Detects new items in /Needs_Action
2. Analyzes what needs to be done
3. Creates Plan.md with step-by-step approach
4. Executes steps (with approval where needed)
5. Updates Dashboard
6. Moves completed items to /Done

RALPH WIGGUM PATTERN:
- Named after the Simpsons character who keeps trying
- Claude keeps iterating until task is complete
- Uses a "stop hook" to know when to stop
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Orchestrator')


class TaskPriority:
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class AIEmployeeOrchestrator:
    """
    Central orchestrator for the AI Employee system.

    Responsibilities:
    1. Monitor /Needs_Action for new tasks
    2. Create execution plans (Plan.md files)
    3. Coordinate watchers and MCP servers
    4. Track task progress
    5. Update Dashboard
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval

        # Key folders
        self.needs_action = self.vault_path / 'Needs_Action'
        self.in_progress = self.vault_path / 'In_Progress'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.plans = self.vault_path / 'Plans'
        self.logs = self.vault_path / 'Logs'

        # Create folders
        for folder in [self.needs_action, self.in_progress, self.pending_approval,
                       self.approved, self.done, self.plans, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

        # Track active tasks
        self.active_tasks = {}

        logger.info(f"Orchestrator initialized for vault: {vault_path}")

    def scan_needs_action(self) -> List[Dict[str, Any]]:
        """
        Scan /Needs_Action folder for new tasks.
        Returns list of tasks sorted by priority.
        """
        tasks = []

        # Scan all subfolders and root
        for item in self.needs_action.rglob('*.md'):
            try:
                content = item.read_text()
                task = self._parse_task(item, content)
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error parsing {item}: {e}")

        # Sort by priority
        tasks.sort(key=lambda x: x.get('priority_num', 999))

        return tasks

    def _parse_task(self, filepath: Path, content: str) -> Dict[str, Any]:
        """Parse a task file and extract metadata."""
        task = {
            'filepath': filepath,
            'filename': filepath.name,
            'content': content,
            'created': datetime.now().isoformat()
        }

        # Extract frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter = parts[1].strip()
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        task[key.strip()] = value.strip()

        # Set priority number
        priority = task.get('priority', 'medium').lower()
        task['priority_num'] = {
            'urgent': TaskPriority.URGENT,
            'high': TaskPriority.HIGH,
            'medium': TaskPriority.MEDIUM,
            'low': TaskPriority.LOW
        }.get(priority, TaskPriority.MEDIUM)

        return task

    def create_plan(self, task: Dict[str, Any]) -> Path:
        """
        Create a Plan.md file for a task.
        This is the Claude reasoning loop - breaking down complex tasks.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        task_type = task.get('type', 'general')
        plan_filename = f'PLAN_{task_type}_{timestamp}.md'
        plan_path = self.plans / plan_filename

        # Analyze task and create steps
        steps = self._analyze_and_plan(task)

        plan_content = f'''---
task_file: {task['filename']}
task_type: {task_type}
created: {datetime.now().isoformat()}
status: in_progress
---

# Execution Plan

## Original Task
**File:** {task['filename']}
**Type:** {task_type}
**Priority:** {task.get('priority', 'medium')}

## Task Summary
{self._summarize_task(task)}

---

## Execution Steps

'''
        for i, step in enumerate(steps, 1):
            plan_content += f'''### Step {i}: {step['name']}
- **Status:** [ ] Pending
- **Action:** {step['action']}
- **Requires Approval:** {'Yes' if step.get('needs_approval') else 'No'}
{f"- **Details:** {step.get('details', '')}" if step.get('details') else ''}

'''

        plan_content += '''---

## Progress Log

| Time | Step | Status | Notes |
|------|------|--------|-------|

---

## Completion Criteria

- [ ] All steps completed
- [ ] Task file moved to /Done
- [ ] Dashboard updated
- [ ] Any follow-up tasks created

---

*Plan created by AI Employee Orchestrator*
*Last updated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M') + '*\n'

        plan_path.write_text(plan_content)
        logger.info(f"Created plan: {plan_path}")

        return plan_path

    def _analyze_and_plan(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze a task and create execution steps.
        This is where AI reasoning happens.
        """
        task_type = task.get('type', 'general')
        steps = []

        # Email task
        if 'email' in task_type.lower():
            steps = [
                {'name': 'Analyze Email', 'action': 'Read and understand the email content'},
                {'name': 'Determine Response', 'action': 'Decide if reply is needed and what to say'},
                {'name': 'Draft Response', 'action': 'Create draft email in /Pending_Approval', 'needs_approval': True},
                {'name': 'Send Email', 'action': 'Send approved email via MCP server'},
                {'name': 'Archive', 'action': 'Move task to /Done and update Dashboard'}
            ]

        # LinkedIn task
        elif 'linkedin' in task_type.lower():
            steps = [
                {'name': 'Review Notification', 'action': 'Understand what the LinkedIn notification is about'},
                {'name': 'Determine Action', 'action': 'Decide appropriate response'},
                {'name': 'Draft Response', 'action': 'Create response/post in /Pending_Approval', 'needs_approval': True},
                {'name': 'Execute', 'action': 'Post to LinkedIn or send message'},
                {'name': 'Archive', 'action': 'Move to /Done'}
            ]

        # Client inquiry
        elif 'client' in task.get('content', '').lower() or 'project' in task.get('content', '').lower():
            steps = [
                {'name': 'Analyze Inquiry', 'action': 'Understand client needs and project scope'},
                {'name': 'Check Handbook', 'action': 'Review Company_Handbook for pricing and services'},
                {'name': 'Prepare Proposal', 'action': 'Draft project proposal', 'needs_approval': True},
                {'name': 'Send Response', 'action': 'Email proposal to client'},
                {'name': 'Create Follow-up', 'action': 'Schedule follow-up reminder'},
                {'name': 'Archive', 'action': 'Move to /Done, add to CRM'}
            ]

        # General task
        else:
            steps = [
                {'name': 'Analyze Task', 'action': 'Understand what needs to be done'},
                {'name': 'Plan Approach', 'action': 'Determine best way to complete task'},
                {'name': 'Execute', 'action': 'Complete the task'},
                {'name': 'Verify', 'action': 'Confirm task is complete'},
                {'name': 'Archive', 'action': 'Move to /Done'}
            ]

        return steps

    def _summarize_task(self, task: Dict[str, Any]) -> str:
        """Create a brief summary of the task."""
        content = task.get('content', '')

        # Extract first meaningful paragraph
        lines = content.split('\n')
        summary_lines = []

        for line in lines:
            if line.strip() and not line.startswith('---') and not line.startswith('#'):
                summary_lines.append(line.strip())
                if len(summary_lines) >= 3:
                    break

        return '\n'.join(summary_lines) or 'No summary available'

    def update_dashboard(self):
        """Update Dashboard.md with current status."""
        dashboard_path = self.vault_path / 'Dashboard.md'

        if not dashboard_path.exists():
            logger.warning("Dashboard.md not found")
            return

        # Count items in each folder
        needs_action_count = len(list(self.needs_action.rglob('*.md')))
        in_progress_count = len(list(self.in_progress.glob('*.md')))
        pending_approval_count = len(list(self.pending_approval.glob('*.md')))
        done_today = len([f for f in self.done.glob('*.md')
                          if datetime.fromtimestamp(f.stat().st_mtime).date() == datetime.now().date()])

        # Update last updated timestamp
        content = dashboard_path.read_text()
        content = self._update_dashboard_field(content, 'Last Updated',
                                                datetime.now().strftime('%Y-%m-%d %H:%M PM'))

        dashboard_path.write_text(content)
        logger.info("Dashboard updated")

    def _update_dashboard_field(self, content: str, field: str, value: str) -> str:
        """Update a specific field in the dashboard."""
        import re
        pattern = rf'\*\*{field}:\*\*\s*.+'
        replacement = f'**{field}:** {value}'
        return re.sub(pattern, replacement, content)

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single task through the workflow.
        """
        logger.info(f"Processing task: {task['filename']}")

        result = {
            'task': task['filename'],
            'status': 'started',
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Create execution plan
            plan_path = self.create_plan(task)
            result['plan'] = str(plan_path)

            # Move task to In_Progress
            dest = self.in_progress / task['filename']
            task['filepath'].rename(dest)
            result['status'] = 'in_progress'

            # Log the action
            self._log_action('task_started', task['filename'])

        except Exception as e:
            logger.error(f"Error processing task: {e}")
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def _log_action(self, action: str, details: str):
        """Log orchestrator actions."""
        log_file = self.logs / f'orchestrator_{datetime.now().strftime("%Y%m%d")}.md'

        with open(log_file, 'a') as f:
            f.write(f"\n## {datetime.now().strftime('%H:%M:%S')} - {action}\n")
            f.write(f"- {details}\n")

    def run_cycle(self) -> List[Dict[str, Any]]:
        """
        Run one cycle of the orchestrator.
        Returns list of processed tasks.
        """
        results = []

        # Scan for new tasks
        tasks = self.scan_needs_action()

        if tasks:
            logger.info(f"Found {len(tasks)} tasks to process")

            # Process highest priority task first
            task = tasks[0]
            result = self.process_task(task)
            results.append(result)

        # Update dashboard
        self.update_dashboard()

        return results

    def run(self):
        """
        Run the orchestrator continuously.
        This is the "Ralph Wiggum" loop - keeps going until stopped.
        """
        logger.info("=" * 50)
        logger.info("AI Employee Orchestrator Started")
        logger.info("=" * 50)
        logger.info(f"Vault: {self.vault_path}")
        logger.info(f"Check interval: {self.check_interval}s")
        logger.info("=" * 50)

        while True:
            try:
                results = self.run_cycle()
                if results:
                    for result in results:
                        logger.info(f"Processed: {result}")
            except KeyboardInterrupt:
                logger.info("Orchestrator stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in orchestrator cycle: {e}")

            time.sleep(self.check_interval)


def demo_orchestrator(vault_path: str):
    """Create sample tasks to demonstrate the orchestrator."""
    orchestrator = AIEmployeeOrchestrator(vault_path)

    # Create a sample email task
    sample_email = orchestrator.needs_action / 'Emails' / 'SAMPLE_EMAIL_001.md'
    sample_email.parent.mkdir(parents=True, exist_ok=True)

    sample_email.write_text('''---
type: email
from: potential.client@example.com
subject: Interested in AI Automation
received: 2026-01-19T14:00:00
priority: high
status: pending
---

# New Email - Client Inquiry

## From
**potential.client@example.com**
CEO at Example Corp

## Subject
Interested in AI Automation

## Content
Hi,

I saw your portfolio and I'm impressed with your AI automation projects.

We're an e-commerce company looking to:
1. Automate customer service responses
2. Set up order tracking notifications
3. Build an inventory management system

What would something like this cost?

Best,
John Smith
Example Corp

---

## Suggested Actions

- [ ] Reply to sender
- [ ] Create project proposal
- [ ] Schedule call

''')

    print("✅ Sample task created!")
    print(f"   Location: {sample_email}")
    print("\nRun the orchestrator to see it process the task:")
    print(f"   python orchestrator.py {vault_path}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <vault_path> [--demo]")
        sys.exit(1)

    vault_path = sys.argv[1]

    if '--demo' in sys.argv:
        demo_orchestrator(vault_path)
    else:
        orchestrator = AIEmployeeOrchestrator(vault_path)
        print(f"Starting Orchestrator for: {vault_path}")
        print("Press Ctrl+C to stop")
        orchestrator.run()
