"""
Ralph Wiggum Loop - Gold Tier Component
========================================
Named after the Simpsons character who keeps trying no matter what.

This is the PERSISTENCE layer that keeps Claude working until a task is DONE.

How it works:
1. Claude picks up a task from /Needs_Action
2. Creates a Plan.md with steps
3. Executes step by step
4. If step fails → retry with different approach
5. If needs approval → wait, then continue
6. Only stops when ALL steps complete or max retries hit

This solves the "lazy agent" problem where AI gives up after one try.
"""

import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('RalphWiggum')


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


class RalphWiggumLoop:
    """
    Persistent task execution loop.

    "Me fail English? That's unpossible!" - Ralph Wiggum

    This loop keeps trying until the task is done or we hit max retries.
    """

    def __init__(self, vault_path: str, max_retries: int = 3,
                 retry_delay: int = 60, approval_check_interval: int = 30):
        self.vault_path = Path(vault_path)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.approval_check_interval = approval_check_interval

        # Folders
        self.needs_action = self.vault_path / 'Needs_Action'
        self.in_progress = self.vault_path / 'In_Progress'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.failed = self.vault_path / 'Failed'
        self.plans = self.vault_path / 'Plans'
        self.logs = self.vault_path / 'Logs' / 'RalphWiggum'

        # Create folders
        for folder in [self.failed, self.logs]:
            folder.mkdir(parents=True, exist_ok=True)

        # Action handlers (registered by other components)
        self.action_handlers: Dict[str, Callable] = {}

        # Current task state
        self.current_task = None
        self.current_plan = None

        logger.info("Ralph Wiggum Loop initialized - I'm helping!")

    def register_handler(self, action_type: str, handler: Callable):
        """Register a handler for a specific action type."""
        self.action_handlers[action_type] = handler
        logger.info(f"Registered handler: {action_type}")

    def execute_task(self, task_file: Path) -> Dict[str, Any]:
        """
        Execute a complete task with persistence.
        This is the main Ralph Wiggum loop.
        """
        task_id = task_file.stem
        logger.info(f"Starting task: {task_id}")

        result = {
            "task_id": task_id,
            "status": TaskStatus.IN_PROGRESS.value,
            "started": datetime.now().isoformat(),
            "steps_completed": 0,
            "steps_total": 0,
            "retries": 0,
            "errors": []
        }

        try:
            # Step 1: Read and parse the task
            task_content = task_file.read_text()
            task_data = self._parse_task(task_content)

            # Step 2: Create or load execution plan
            plan = self._get_or_create_plan(task_file, task_data)
            result["steps_total"] = len(plan["steps"])

            # Step 3: Move task to In_Progress
            in_progress_path = self.in_progress / task_file.name
            if task_file.exists():
                task_file.rename(in_progress_path)

            # Step 4: Execute each step with retry logic
            for i, step in enumerate(plan["steps"]):
                step_result = self._execute_step_with_retry(step, task_data)

                plan["steps"][i]["status"] = step_result["status"]
                plan["steps"][i]["result"] = step_result

                # Update plan file
                self._save_plan(plan)

                if step_result["status"] == StepStatus.COMPLETED.value:
                    result["steps_completed"] += 1
                elif step_result["status"] == StepStatus.FAILED.value:
                    result["errors"].append(step_result.get("error", "Unknown error"))
                    # Continue to next step (graceful degradation)

            # Step 5: Check if task is complete
            completed_steps = sum(1 for s in plan["steps"]
                                  if s.get("status") == StepStatus.COMPLETED.value)

            if completed_steps == len(plan["steps"]):
                result["status"] = TaskStatus.COMPLETED.value
                # Move to Done
                done_path = self.done / task_file.name
                if in_progress_path.exists():
                    in_progress_path.rename(done_path)
                logger.info(f"Task completed: {task_id}")
            else:
                result["status"] = TaskStatus.FAILED.value
                # Move to Failed
                failed_path = self.failed / task_file.name
                if in_progress_path.exists():
                    in_progress_path.rename(failed_path)
                logger.warning(f"Task partially failed: {task_id}")

        except Exception as e:
            logger.error(f"Task execution error: {e}")
            result["status"] = TaskStatus.FAILED.value
            result["errors"].append(str(e))

        result["completed"] = datetime.now().isoformat()

        # Log the result
        self._log_execution(result)

        return result

    def _execute_step_with_retry(self, step: Dict, task_data: Dict) -> Dict[str, Any]:
        """
        Execute a single step with retry logic.
        This is where the "keep trying" magic happens.
        """
        step_name = step.get("name", "Unknown")
        action = step.get("action", "")
        needs_approval = step.get("needs_approval", False)

        result = {
            "step": step_name,
            "status": StepStatus.PENDING.value,
            "attempts": 0,
            "started": datetime.now().isoformat()
        }

        for attempt in range(self.max_retries):
            result["attempts"] = attempt + 1
            logger.info(f"Executing step '{step_name}' (attempt {attempt + 1}/{self.max_retries})")

            try:
                # Check if this step needs approval
                if needs_approval:
                    approval_result = self._wait_for_approval(step, task_data)
                    if not approval_result["approved"]:
                        result["status"] = StepStatus.SKIPPED.value
                        result["reason"] = "Rejected by human"
                        return result

                # Execute the action
                action_result = self._execute_action(step, task_data)

                if action_result.get("success", False):
                    result["status"] = StepStatus.COMPLETED.value
                    result["result"] = action_result
                    result["completed"] = datetime.now().isoformat()
                    return result
                else:
                    # Action failed, will retry
                    result["last_error"] = action_result.get("error", "Unknown error")
                    logger.warning(f"Step failed: {result['last_error']}")

            except Exception as e:
                result["last_error"] = str(e)
                logger.error(f"Step exception: {e}")

            # Wait before retry
            if attempt < self.max_retries - 1:
                logger.info(f"Waiting {self.retry_delay}s before retry...")
                time.sleep(self.retry_delay)

        # All retries exhausted
        result["status"] = StepStatus.FAILED.value
        result["error"] = result.get("last_error", "Max retries exceeded")
        return result

    def _wait_for_approval(self, step: Dict, task_data: Dict) -> Dict[str, Any]:
        """
        Wait for human approval before executing sensitive action.
        Creates approval request and polls for response.
        """
        step_name = step.get("name", "Unknown")

        # Create approval request
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        approval_file = self.pending_approval / f'APPROVAL_{step_name}_{timestamp}.md'

        content = f'''---
type: step_approval
step: {step_name}
task: {task_data.get('type', 'unknown')}
created: {datetime.now().isoformat()}
status: pending_approval
---

# Step Approval Required

## Step
**{step_name}**

## Action
{step.get('action', 'No description')}

## Context
This step requires your approval before the AI Employee can proceed.

---

## Actions

- [ ] **APPROVE** - Execute this step
- [ ] **REJECT** - Skip this step

---

*Waiting for human approval...*
'''
        approval_file.write_text(content)
        logger.info(f"Created approval request: {approval_file}")

        # Poll for approval
        max_wait = 3600  # 1 hour max wait
        waited = 0

        while waited < max_wait:
            # Check if file was moved to Approved
            approved_path = self.approved / approval_file.name
            if approved_path.exists():
                logger.info(f"Step approved: {step_name}")
                return {"approved": True}

            # Check if file was moved to Rejected (or modified with reject)
            if not approval_file.exists():
                # File was moved somewhere - check if it's in a reject folder
                logger.info(f"Step rejected or moved: {step_name}")
                return {"approved": False}

            # Check if file content has [x] APPROVE or [x] REJECT
            if approval_file.exists():
                content = approval_file.read_text().lower()
                if '[x]' in content and 'approve' in content:
                    approval_file.rename(approved_path)
                    return {"approved": True}
                elif '[x]' in content and 'reject' in content:
                    approval_file.unlink()
                    return {"approved": False}

            time.sleep(self.approval_check_interval)
            waited += self.approval_check_interval

        # Timeout - treat as rejection
        logger.warning(f"Approval timeout for step: {step_name}")
        return {"approved": False, "reason": "timeout"}

    def _execute_action(self, step: Dict, task_data: Dict) -> Dict[str, Any]:
        """Execute an action using registered handlers."""
        action_type = step.get("action_type", "default")

        if action_type in self.action_handlers:
            handler = self.action_handlers[action_type]
            return handler(step, task_data)

        # Default: just mark as done (manual action)
        return {
            "success": True,
            "message": f"Step '{step.get('name')}' marked as complete (manual)"
        }

    def _parse_task(self, content: str) -> Dict[str, Any]:
        """Parse task file content."""
        task = {"raw": content}

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                for line in parts[1].strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        task[key.strip()] = value.strip()

        return task

    def _get_or_create_plan(self, task_file: Path, task_data: Dict) -> Dict:
        """Get existing plan or create new one."""
        plan_file = self.plans / f'PLAN_{task_file.stem}.json'

        if plan_file.exists():
            with open(plan_file, 'r') as f:
                return json.load(f)

        # Create new plan
        plan = {
            "task_file": task_file.name,
            "task_type": task_data.get("type", "general"),
            "created": datetime.now().isoformat(),
            "steps": self._generate_steps(task_data)
        }

        self._save_plan(plan)
        return plan

    def _generate_steps(self, task_data: Dict) -> List[Dict]:
        """Generate execution steps based on task type."""
        task_type = task_data.get("type", "general").lower()

        if "email" in task_type:
            return [
                {"name": "Analyze", "action": "Read and understand content", "status": "pending"},
                {"name": "Draft", "action": "Create response draft", "status": "pending"},
                {"name": "Approve", "action": "Get human approval", "needs_approval": True, "status": "pending"},
                {"name": "Send", "action": "Send the email", "action_type": "send_email", "status": "pending"},
                {"name": "Archive", "action": "Move to Done", "status": "pending"}
            ]
        elif "linkedin" in task_type or "social" in task_type:
            return [
                {"name": "Create", "action": "Create post content", "status": "pending"},
                {"name": "Approve", "action": "Get human approval", "needs_approval": True, "status": "pending"},
                {"name": "Post", "action": "Publish to platform", "action_type": "social_post", "status": "pending"},
                {"name": "Archive", "action": "Move to Done", "status": "pending"}
            ]
        else:
            return [
                {"name": "Analyze", "action": "Understand the task", "status": "pending"},
                {"name": "Execute", "action": "Complete the task", "status": "pending"},
                {"name": "Verify", "action": "Confirm completion", "status": "pending"},
                {"name": "Archive", "action": "Move to Done", "status": "pending"}
            ]

    def _save_plan(self, plan: Dict):
        """Save plan to file."""
        plan_file = self.plans / f'PLAN_{plan["task_file"].replace(".md", "")}.json'
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)

    def _log_execution(self, result: Dict):
        """Log execution result."""
        log_file = self.logs / f'execution_{datetime.now().strftime("%Y%m%d")}.json'

        logs = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)

        logs.append(result)

        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def run_loop(self):
        """
        Main Ralph Wiggum loop - continuously process tasks.
        "I'm learnding!" - Ralph
        """
        logger.info("=" * 50)
        logger.info("Ralph Wiggum Loop Starting")
        logger.info("'I'm helping!' - Ralph Wiggum")
        logger.info("=" * 50)

        while True:
            try:
                # Find tasks to process
                tasks = list(self.needs_action.rglob('*.md'))

                if tasks:
                    # Process first task
                    task = tasks[0]
                    logger.info(f"Found task: {task.name}")
                    result = self.execute_task(task)
                    logger.info(f"Task result: {result['status']}")
                else:
                    logger.debug("No tasks found, waiting...")

            except KeyboardInterrupt:
                logger.info("Ralph Wiggum Loop stopped by user")
                break
            except Exception as e:
                logger.error(f"Loop error: {e}")

            time.sleep(60)  # Check every minute


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ralph_wiggum_loop.py <vault_path>")
        sys.exit(1)

    vault_path = sys.argv[1]
    loop = RalphWiggumLoop(vault_path)

    print("Ralph Wiggum Loop")
    print("=" * 40)
    print(f"Vault: {vault_path}")
    print("'Me fail English? That's unpossible!'")
    print("=" * 40)
    print("\nPress Ctrl+C to stop")

    loop.run_loop()
