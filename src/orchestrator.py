#!/usr/bin/env python3
"""
AI Employee Orchestrator - The Central Nervous System
======================================================
This is the main orchestration engine that coordinates all watchers,
processes events, and triggers Claude Code for reasoning and actions.

The "Ralph Wiggum Loop" - Persistent operation that keeps your AI Employee running.
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nerve_center/logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AIEmployee')


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class Config:
    """Central configuration for the AI Employee system."""

    # Paths
    nerve_center_path: Path = Path("nerve_center")
    inbox_path: Path = Path("nerve_center/inbox")
    processed_path: Path = Path("nerve_center/processed")
    logs_path: Path = Path("nerve_center/logs")
    skills_path: Path = Path("nerve_center/skills")

    # Timing (in seconds)
    watcher_interval: int = 30  # How often watchers check for new events
    processing_interval: int = 60  # How often to process the inbox
    dashboard_update_interval: int = 300  # Dashboard refresh (5 minutes)
    health_check_interval: int = 120  # System health check (2 minutes)

    # Claude Code settings
    claude_command: str = "claude"
    claude_timeout: int = 300  # 5 minutes max per task

    # Human-in-the-loop settings
    require_approval_above: float = 100.0  # Dollar amount requiring approval
    auto_send_emails: bool = False  # If True, sends without approval

    # Rate limiting
    max_api_calls_per_hour: int = 100
    max_emails_per_hour: int = 20

    def __post_init__(self):
        """Ensure all directories exist."""
        for path in [self.nerve_center_path, self.inbox_path,
                     self.processed_path, self.logs_path, self.skills_path]:
            path.mkdir(parents=True, exist_ok=True)


# =============================================================================
# EVENT SYSTEM
# =============================================================================

class EventType(Enum):
    """Types of events the system can handle."""
    EMAIL_RECEIVED = "email_received"
    EMAIL_SENT = "email_sent"
    MESSAGE_RECEIVED = "message_received"
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    CALENDAR_EVENT = "calendar_event"
    INVOICE_DETECTED = "invoice_detected"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_GRANTED = "approval_granted"
    ERROR = "error"
    SYSTEM_HEALTH = "system_health"
    SCHEDULED_TASK = "scheduled_task"


@dataclass
class Event:
    """Represents an event in the system."""
    id: str
    type: EventType
    source: str
    timestamp: datetime
    data: Dict[str, Any]
    priority: int = 5  # 1 = highest, 10 = lowest
    requires_approval: bool = False
    processed: bool = False

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "priority": self.priority,
            "requires_approval": self.requires_approval,
            "processed": self.processed
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data["data"],
            priority=data.get("priority", 5),
            requires_approval=data.get("requires_approval", False),
            processed=data.get("processed", False)
        )

    def save(self, path: Path):
        """Save event to a JSON file."""
        filepath = path / f"{self.id}.json"
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Path) -> 'Event':
        """Load event from a JSON file."""
        with open(filepath, 'r') as f:
            return cls.from_dict(json.load(f))


def generate_event_id(event_type: str, source: str) -> str:
    """Generate a unique event ID."""
    timestamp = datetime.now().isoformat()
    unique_string = f"{event_type}-{source}-{timestamp}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]


# =============================================================================
# BASE WATCHER
# =============================================================================

class BaseWatcher(ABC):
    """Abstract base class for all watchers."""

    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f'Watcher.{name}')
        self.running = False
        self.last_check = None
        self.events_detected = 0
        self.errors = 0

    @abstractmethod
    async def check(self) -> List[Event]:
        """Check for new events. Must be implemented by subclasses."""
        pass

    async def run(self, event_queue: asyncio.Queue):
        """Main watcher loop."""
        self.running = True
        self.logger.info(f"Starting {self.name} watcher")

        while self.running:
            try:
                events = await self.check()
                self.last_check = datetime.now()

                for event in events:
                    self.events_detected += 1
                    await event_queue.put(event)
                    self.logger.info(f"Event detected: {event.type.value} - {event.id}")

            except Exception as e:
                self.errors += 1
                self.logger.error(f"Error in {self.name} watcher: {e}")

            await asyncio.sleep(self.config.watcher_interval)

    def stop(self):
        """Stop the watcher."""
        self.running = False
        self.logger.info(f"Stopping {self.name} watcher")

    def get_status(self) -> Dict:
        """Get watcher status for dashboard."""
        return {
            "name": self.name,
            "running": self.running,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "events_detected": self.events_detected,
            "errors": self.errors
        }


# =============================================================================
# WATCHER IMPLEMENTATIONS
# =============================================================================

class FileSystemWatcher(BaseWatcher):
    """Watches the inbox folder for new files."""

    def __init__(self, config: Config):
        super().__init__("FileSystem", config)
        self.seen_files: set = set()
        self._scan_existing()

    def _scan_existing(self):
        """Record existing files to avoid processing them as new."""
        if self.config.inbox_path.exists():
            for file in self.config.inbox_path.iterdir():
                if file.is_file():
                    self.seen_files.add(str(file))

    async def check(self) -> List[Event]:
        events = []

        if not self.config.inbox_path.exists():
            return events

        for file in self.config.inbox_path.iterdir():
            if file.is_file() and str(file) not in self.seen_files:
                self.seen_files.add(str(file))

                # Determine event type based on file
                event_type = EventType.FILE_CREATED
                if "invoice" in file.name.lower():
                    event_type = EventType.INVOICE_DETECTED

                event = Event(
                    id=generate_event_id("file", file.name),
                    type=event_type,
                    source="filesystem",
                    timestamp=datetime.now(),
                    data={
                        "filename": file.name,
                        "filepath": str(file),
                        "size": file.stat().st_size
                    },
                    priority=5 if event_type == EventType.FILE_CREATED else 3
                )
                events.append(event)

        return events


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail for new emails.
    Requires: pip install google-auth google-auth-oauthlib google-api-python-client
    """

    def __init__(self, config: Config, credentials_path: str = "config/gmail_credentials.json"):
        super().__init__("Gmail", config)
        self.credentials_path = credentials_path
        self.service = None
        self.last_history_id = None
        self.seen_message_ids: set = set()

    async def _get_service(self):
        """Initialize Gmail API service."""
        if self.service:
            return self.service

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
            creds = None
            token_path = "config/gmail_token.json"

            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)

                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            self.service = build('gmail', 'v1', credentials=creds)
            return self.service

        except ImportError:
            self.logger.warning("Gmail API libraries not installed. Run: pip install google-auth google-auth-oauthlib google-api-python-client")
            return None
        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail service: {e}")
            return None

    async def check(self) -> List[Event]:
        events = []
        service = await self._get_service()

        if not service:
            return events

        try:
            # Get recent unread messages
            results = service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=10
            ).execute()

            messages = results.get('messages', [])

            for msg in messages:
                if msg['id'] in self.seen_message_ids:
                    continue

                self.seen_message_ids.add(msg['id'])

                # Get message details
                message = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in message['payload']['headers']}

                # Determine priority based on content
                priority = 5
                subject = headers.get('Subject', '').lower()
                if any(word in subject for word in ['urgent', 'asap', 'important']):
                    priority = 1
                elif any(word in subject for word in ['invoice', 'payment', 'bill']):
                    priority = 2

                event = Event(
                    id=generate_event_id("email", msg['id']),
                    type=EventType.EMAIL_RECEIVED,
                    source="gmail",
                    timestamp=datetime.now(),
                    data={
                        "message_id": msg['id'],
                        "from": headers.get('From', ''),
                        "subject": headers.get('Subject', ''),
                        "date": headers.get('Date', ''),
                        "snippet": message.get('snippet', '')
                    },
                    priority=priority
                )
                events.append(event)

        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")

        return events


class ScheduledTaskWatcher(BaseWatcher):
    """Watches for scheduled tasks that need to run."""

    def __init__(self, config: Config):
        super().__init__("Scheduler", config)
        self.tasks: List[Dict] = []
        self._load_schedule()

    def _load_schedule(self):
        """Load scheduled tasks from configuration."""
        schedule_file = self.config.nerve_center_path / "schedule.json"
        if schedule_file.exists():
            with open(schedule_file, 'r') as f:
                self.tasks = json.load(f)

    def add_task(self, name: str, cron: str, action: str):
        """Add a scheduled task."""
        self.tasks.append({
            "name": name,
            "cron": cron,
            "action": action,
            "last_run": None
        })
        self._save_schedule()

    def _save_schedule(self):
        """Save scheduled tasks to file."""
        schedule_file = self.config.nerve_center_path / "schedule.json"
        with open(schedule_file, 'w') as f:
            json.dump(self.tasks, f, indent=2)

    async def check(self) -> List[Event]:
        events = []
        now = datetime.now()

        for task in self.tasks:
            # Simple time-based check (for demo - use croniter for real cron parsing)
            if self._should_run(task, now):
                event = Event(
                    id=generate_event_id("schedule", task['name']),
                    type=EventType.SCHEDULED_TASK,
                    source="scheduler",
                    timestamp=now,
                    data={
                        "task_name": task['name'],
                        "action": task['action']
                    },
                    priority=3
                )
                events.append(event)
                task['last_run'] = now.isoformat()

        self._save_schedule()
        return events

    def _should_run(self, task: Dict, now: datetime) -> bool:
        """Check if a task should run now."""
        if task.get('last_run'):
            last_run = datetime.fromisoformat(task['last_run'])
            # Simple hourly check for demo
            if (now - last_run).total_seconds() < 3600:
                return False
        return True


# =============================================================================
# CLAUDE CODE INTEGRATION
# =============================================================================

class ClaudeCodeRunner:
    """Handles interaction with Claude Code CLI."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger('ClaudeCode')
        self.api_calls = 0
        self.last_reset = datetime.now()

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.now()
        if (now - self.last_reset).total_seconds() > 3600:
            self.api_calls = 0
            self.last_reset = now

        return self.api_calls < self.config.max_api_calls_per_hour

    async def process_event(self, event: Event) -> Dict:
        """Process an event using Claude Code."""
        if not self._check_rate_limit():
            self.logger.warning("Rate limit reached, skipping event")
            return {"status": "rate_limited", "event_id": event.id}

        self.api_calls += 1

        # Build the prompt for Claude
        prompt = self._build_prompt(event)

        try:
            # Run Claude Code
            result = await self._run_claude(prompt)

            return {
                "status": "success",
                "event_id": event.id,
                "result": result
            }
        except Exception as e:
            self.logger.error(f"Error running Claude Code: {e}")
            return {
                "status": "error",
                "event_id": event.id,
                "error": str(e)
            }

    def _build_prompt(self, event: Event) -> str:
        """Build a prompt for Claude based on the event type."""
        base_context = f"""
You are an AI Employee assistant. Process the following event and take appropriate action.
Refer to the Company Handbook at nerve_center/Company_Handbook.md for guidelines.
Update the Dashboard at nerve_center/Dashboard.md with any relevant changes.

Event Type: {event.type.value}
Source: {event.source}
Priority: {event.priority}
Timestamp: {event.timestamp.isoformat()}

Event Data:
{json.dumps(event.data, indent=2)}
"""

        # Add type-specific instructions
        instructions = {
            EventType.EMAIL_RECEIVED: """
Analyze this email and:
1. Categorize it (urgent/normal/low priority)
2. Determine if it requires a response
3. If response needed, draft a reply following the Company Handbook style guide
4. Update Dashboard with this email info
5. If it's an invoice or payment-related, flag for financial review
""",
            EventType.INVOICE_DETECTED: """
Process this invoice:
1. Extract: vendor name, amount, due date, invoice number
2. Check if amount exceeds approval threshold ($100)
3. If above threshold, create approval request
4. Log invoice details to Dashboard
5. Add to financial tracking
""",
            EventType.FILE_CREATED: """
Process this new file:
1. Analyze the file content/type
2. Categorize appropriately
3. If it requires action, create a task
4. Update Dashboard with file info
5. Move to processed folder if complete
""",
            EventType.SCHEDULED_TASK: """
Execute this scheduled task:
1. Read the task action from the event data
2. Perform the required action
3. Log the result
4. Update Dashboard with completion status
"""
        }

        return base_context + instructions.get(event.type, "\nProcess this event appropriately.")

    async def _run_claude(self, prompt: str) -> str:
        """Execute Claude Code with the given prompt."""
        # Write prompt to temp file
        prompt_file = self.config.logs_path / "current_prompt.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)

        try:
            # Run Claude Code in non-interactive mode
            process = await asyncio.create_subprocess_exec(
                self.config.claude_command,
                "--print",  # Print output without interactive mode
                "-p", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.config.nerve_center_path.parent)
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.claude_timeout
            )

            if process.returncode != 0:
                self.logger.error(f"Claude Code error: {stderr.decode()}")
                return f"Error: {stderr.decode()}"

            return stdout.decode()

        except asyncio.TimeoutError:
            self.logger.error("Claude Code timed out")
            return "Error: Claude Code timed out"
        except FileNotFoundError:
            self.logger.error("Claude Code not found. Ensure it's installed and in PATH.")
            return "Error: Claude Code not found"


# =============================================================================
# DASHBOARD MANAGER
# =============================================================================

class DashboardManager:
    """Manages the Dashboard.md file updates."""

    def __init__(self, config: Config):
        self.config = config
        self.dashboard_path = config.nerve_center_path / "Dashboard.md"
        self.logger = logging.getLogger('Dashboard')

    def update_stats(self, stats: Dict):
        """Update dashboard statistics."""
        # This would parse and update the markdown file
        # For now, we'll append to a stats log
        stats_log = self.config.logs_path / "stats.json"

        existing_stats = {}
        if stats_log.exists():
            with open(stats_log, 'r') as f:
                existing_stats = json.load(f)

        existing_stats[datetime.now().isoformat()] = stats

        with open(stats_log, 'w') as f:
            json.dump(existing_stats, f, indent=2)

    def add_activity(self, activity: str, category: str, status: str):
        """Add an activity to the recent activity log."""
        activity_log = self.config.logs_path / "activity.json"

        activities = []
        if activity_log.exists():
            with open(activity_log, 'r') as f:
                activities = json.load(f)

        activities.insert(0, {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "action": activity,
            "status": status
        })

        # Keep only last 100 activities
        activities = activities[:100]

        with open(activity_log, 'w') as f:
            json.dump(activities, f, indent=2)

    def add_pending_approval(self, event: Event):
        """Add an item requiring approval."""
        approval_file = self.config.inbox_path / f"approval_{event.id}.json"

        with open(approval_file, 'w') as f:
            json.dump({
                "event": event.to_dict(),
                "created": datetime.now().isoformat(),
                "status": "pending",
                "approved_by": None,
                "approved_at": None
            }, f, indent=2)


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

class Orchestrator:
    """
    The main orchestrator - coordinates all components.
    This is the "Ralph Wiggum Loop" that keeps everything running.
    """

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger('Orchestrator')

        # Components
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.watchers: List[BaseWatcher] = []
        self.claude_runner = ClaudeCodeRunner(self.config)
        self.dashboard = DashboardManager(self.config)

        # State
        self.running = False
        self.start_time = None
        self.events_processed = 0

        # Initialize watchers
        self._init_watchers()

    def _init_watchers(self):
        """Initialize all watchers."""
        self.watchers = [
            FileSystemWatcher(self.config),
            ScheduledTaskWatcher(self.config),
            # GmailWatcher(self.config),  # Uncomment when credentials are set up
        ]

    async def start(self):
        """Start the orchestrator and all components."""
        self.running = True
        self.start_time = datetime.now()
        self.logger.info("=" * 50)
        self.logger.info("AI Employee Orchestrator Starting")
        self.logger.info("=" * 50)

        # Set up signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                sig, lambda: asyncio.create_task(self.shutdown())
            )

        # Start all components
        tasks = [
            asyncio.create_task(self._run_watchers()),
            asyncio.create_task(self._process_events()),
            asyncio.create_task(self._health_check()),
        ]

        self.logger.info("All components started. AI Employee is now active.")
        self.logger.info(f"Watching: {self.config.inbox_path}")
        self.logger.info("Press Ctrl+C to stop.")

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_watchers(self):
        """Run all watchers concurrently."""
        watcher_tasks = [
            asyncio.create_task(watcher.run(self.event_queue))
            for watcher in self.watchers
        ]
        await asyncio.gather(*watcher_tasks, return_exceptions=True)

    async def _process_events(self):
        """Main event processing loop."""
        while self.running:
            try:
                # Wait for events with timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=self.config.processing_interval
                    )
                except asyncio.TimeoutError:
                    continue

                self.logger.info(f"Processing event: {event.type.value} - {event.id}")

                # Check if approval is required
                if event.requires_approval:
                    self.dashboard.add_pending_approval(event)
                    self.logger.info(f"Event {event.id} requires approval, added to queue")
                    continue

                # Process with Claude Code
                result = await self.claude_runner.process_event(event)

                # Update tracking
                self.events_processed += 1
                self.dashboard.add_activity(
                    f"Processed {event.type.value}",
                    event.source,
                    result.get("status", "unknown")
                )

                # Mark event as processed
                event.processed = True
                event.save(self.config.processed_path)

                self.logger.info(f"Event {event.id} processed: {result.get('status')}")

            except Exception as e:
                self.logger.error(f"Error processing event: {e}")

    async def _health_check(self):
        """Periodic health check and status update."""
        while self.running:
            await asyncio.sleep(self.config.health_check_interval)

            status = {
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
                "events_processed": self.events_processed,
                "queue_size": self.event_queue.qsize(),
                "watchers": [w.get_status() for w in self.watchers],
                "api_calls": self.claude_runner.api_calls
            }

            self.dashboard.update_stats(status)
            self.logger.debug(f"Health check: {status}")

    async def shutdown(self):
        """Gracefully shutdown all components."""
        self.logger.info("Shutting down AI Employee...")
        self.running = False

        # Stop all watchers
        for watcher in self.watchers:
            watcher.stop()

        # Final status update
        self.dashboard.add_activity(
            "System shutdown",
            "orchestrator",
            "completed"
        )

        self.logger.info("AI Employee shutdown complete.")


# =============================================================================
# CLI INTERFACE
# =============================================================================

def print_banner():
    """Print startup banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║     █████╗ ██╗    ███████╗███╗   ███╗██████╗ ██╗      ██╗   ║
    ║    ██╔══██╗██║    ██╔════╝████╗ ████║██╔══██╗██║      ╚██╗  ║
    ║    ███████║██║    █████╗  ██╔████╔██║██████╔╝██║       ╚██╗ ║
    ║    ██╔══██║██║    ██╔══╝  ██║╚██╔╝██║██╔═══╝ ██║       ██╔╝ ║
    ║    ██║  ██║██║    ███████╗██║ ╚═╝ ██║██║     ███████╗██╔╝   ║
    ║    ╚═╝  ╚═╝╚═╝    ╚══════╝╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝    ║
    ║                                                              ║
    ║            Your Personal AI Employee - v1.0.0                ║
    ║                  "I'm helping!" - Ralph                      ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main():
    """Main entry point."""
    print_banner()

    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("""
AI Employee Orchestrator

Usage:
    python orchestrator.py              Start the AI Employee
    python orchestrator.py --help       Show this help message
    python orchestrator.py --status     Show current status
    python orchestrator.py --test       Run in test mode

Environment Variables:
    AI_EMPLOYEE_CONFIG    Path to custom config file
    CLAUDE_COMMAND        Path to Claude Code CLI (default: claude)
""")
            return
        elif sys.argv[1] == "--status":
            config = Config()
            stats_file = config.logs_path / "stats.json"
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                    latest = list(stats.values())[-1] if stats else {}
                    print(f"Last Status: {json.dumps(latest, indent=2)}")
            else:
                print("No status available. Start the orchestrator first.")
            return
        elif sys.argv[1] == "--test":
            print("Running in test mode...")
            config = Config()
            # Create a test event
            test_event = Event(
                id=generate_event_id("test", "cli"),
                type=EventType.FILE_CREATED,
                source="test",
                timestamp=datetime.now(),
                data={"test": True, "message": "This is a test event"}
            )
            test_event.save(config.inbox_path)
            print(f"Test event created: {test_event.id}")
            print("Start the orchestrator to process it.")
            return

    # Start the orchestrator
    orchestrator = Orchestrator()
    await orchestrator.start()


if __name__ == "__main__":
    asyncio.run(main())
