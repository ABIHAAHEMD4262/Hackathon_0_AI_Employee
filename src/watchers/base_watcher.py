"""
Base Watcher Module
===================
Abstract base class for all watchers with common functionality.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import hashlib
from pathlib import Path


class WatcherStatus(Enum):
    """Watcher operational status."""
    INACTIVE = "inactive"
    STARTING = "starting"
    ACTIVE = "active"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"


class EventType(Enum):
    """Types of events the system can handle."""
    # Communication events
    EMAIL_RECEIVED = "email_received"
    EMAIL_SENT = "email_sent"
    WHATSAPP_MESSAGE = "whatsapp_message"
    SLACK_MESSAGE = "slack_message"
    DISCORD_MESSAGE = "discord_message"
    SMS_RECEIVED = "sms_received"

    # Calendar events
    CALENDAR_EVENT_CREATED = "calendar_event_created"
    CALENDAR_EVENT_UPDATED = "calendar_event_updated"
    CALENDAR_EVENT_DELETED = "calendar_event_deleted"
    CALENDAR_REMINDER = "calendar_reminder"

    # File events
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"

    # Financial events
    INVOICE_DETECTED = "invoice_detected"
    PAYMENT_RECEIVED = "payment_received"
    EXPENSE_DETECTED = "expense_detected"

    # Social media events
    TWITTER_MENTION = "twitter_mention"
    TWITTER_DM = "twitter_dm"
    LINKEDIN_MESSAGE = "linkedin_message"
    LINKEDIN_NOTIFICATION = "linkedin_notification"

    # Task events
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_OVERDUE = "task_overdue"

    # System events
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
    channel: str = "unknown"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "priority": self.priority,
            "requires_approval": self.requires_approval,
            "processed": self.processed,
            "channel": self.channel
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
            processed=data.get("processed", False),
            channel=data.get("channel", "unknown")
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


def generate_event_id(event_type: str, source: str, unique_data: str = "") -> str:
    """Generate a unique event ID."""
    timestamp = datetime.now().isoformat()
    unique_string = f"{event_type}-{source}-{timestamp}-{unique_data}"
    return hashlib.sha256(unique_string.encode()).hexdigest()[:16]


@dataclass
class WatcherMetrics:
    """Metrics tracked by each watcher."""
    events_detected: int = 0
    events_processed: int = 0
    errors: int = 0
    last_check: Optional[datetime] = None
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    uptime_seconds: float = 0
    avg_check_duration_ms: float = 0
    checks_performed: int = 0


class BaseWatcher(ABC):
    """
    Abstract base class for all watchers.

    Watchers are responsible for:
    1. Monitoring a specific data source (email, messages, files, etc.)
    2. Detecting new events
    3. Creating Event objects
    4. Pushing events to the processing queue
    """

    def __init__(
        self,
        name: str,
        check_interval: int = 30,
        config: Optional[Dict] = None
    ):
        self.name = name
        self.check_interval = check_interval
        self.config = config or {}

        # State
        self.status = WatcherStatus.INACTIVE
        self.running = False
        self.start_time: Optional[datetime] = None

        # Metrics
        self.metrics = WatcherMetrics()

        # Logging
        self.logger = logging.getLogger(f'Watcher.{name}')

        # Deduplication
        self._seen_ids: set = set()
        self._max_seen_ids = 10000

    @abstractmethod
    async def check(self) -> List[Event]:
        """
        Check for new events. Must be implemented by subclasses.

        Returns:
            List of Event objects detected since last check
        """
        pass

    @abstractmethod
    async def setup(self) -> bool:
        """
        Initialize the watcher (authenticate, connect, etc.)

        Returns:
            True if setup successful, False otherwise
        """
        pass

    @abstractmethod
    async def teardown(self):
        """Clean up resources when stopping."""
        pass

    async def run(self, event_queue: asyncio.Queue):
        """Main watcher loop."""
        self.status = WatcherStatus.STARTING
        self.start_time = datetime.now()

        # Initialize
        if not await self.setup():
            self.status = WatcherStatus.ERROR
            self.logger.error(f"Failed to initialize {self.name} watcher")
            return

        self.status = WatcherStatus.ACTIVE
        self.running = True
        self.logger.info(f"Started {self.name} watcher (interval: {self.check_interval}s)")

        while self.running:
            check_start = datetime.now()

            try:
                events = await self.check()

                for event in events:
                    # Deduplicate
                    if event.id in self._seen_ids:
                        continue

                    self._seen_ids.add(event.id)
                    self._cleanup_seen_ids()

                    # Track metrics
                    self.metrics.events_detected += 1

                    # Push to queue
                    await event_queue.put(event)
                    self.logger.info(f"Event: {event.type.value} - {event.id[:8]}...")

                self.metrics.last_check = datetime.now()
                self.metrics.checks_performed += 1

                # Update average check duration
                duration = (datetime.now() - check_start).total_seconds() * 1000
                self.metrics.avg_check_duration_ms = (
                    (self.metrics.avg_check_duration_ms * (self.metrics.checks_performed - 1) + duration)
                    / self.metrics.checks_performed
                )

            except Exception as e:
                self.metrics.errors += 1
                self.metrics.last_error = str(e)
                self.metrics.last_error_time = datetime.now()
                self.logger.error(f"Error in {self.name} watcher: {e}")

            # Update uptime
            if self.start_time:
                self.metrics.uptime_seconds = (datetime.now() - self.start_time).total_seconds()

            await asyncio.sleep(self.check_interval)

        # Cleanup
        await self.teardown()
        self.status = WatcherStatus.STOPPED

    def _cleanup_seen_ids(self):
        """Prevent memory bloat from seen IDs."""
        if len(self._seen_ids) > self._max_seen_ids:
            # Remove oldest half
            to_remove = list(self._seen_ids)[:self._max_seen_ids // 2]
            for item in to_remove:
                self._seen_ids.discard(item)

    def stop(self):
        """Stop the watcher."""
        self.status = WatcherStatus.STOPPING
        self.running = False
        self.logger.info(f"Stopping {self.name} watcher")

    def get_status(self) -> Dict:
        """Get watcher status for dashboard."""
        return {
            "name": self.name,
            "status": self.status.value,
            "running": self.running,
            "last_check": self.metrics.last_check.isoformat() if self.metrics.last_check else None,
            "events_detected": self.metrics.events_detected,
            "errors": self.metrics.errors,
            "uptime_seconds": self.metrics.uptime_seconds,
            "avg_check_ms": round(self.metrics.avg_check_duration_ms, 2),
            "last_error": self.metrics.last_error,
        }

    def is_healthy(self) -> bool:
        """Check if watcher is operating normally."""
        if self.status != WatcherStatus.ACTIVE:
            return False

        # Check for recent errors (more than 5 in last hour)
        if self.metrics.errors > 5:
            return False

        # Check if checks are happening
        if self.metrics.last_check:
            time_since_check = (datetime.now() - self.metrics.last_check).total_seconds()
            if time_since_check > self.check_interval * 3:
                return False

        return True


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int, period_seconds: int):
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls: List[datetime] = []

    async def acquire(self):
        """Wait if rate limit exceeded."""
        now = datetime.now()

        # Remove old calls
        self.calls = [
            c for c in self.calls
            if (now - c).total_seconds() < self.period
        ]

        if len(self.calls) >= self.max_calls:
            # Wait for oldest call to expire
            wait_time = self.period - (now - self.calls[0]).total_seconds()
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        self.calls.append(datetime.now())

    @property
    def remaining(self) -> int:
        """Get remaining calls in current period."""
        now = datetime.now()
        active_calls = len([
            c for c in self.calls
            if (now - c).total_seconds() < self.period
        ])
        return max(0, self.max_calls - active_calls)
