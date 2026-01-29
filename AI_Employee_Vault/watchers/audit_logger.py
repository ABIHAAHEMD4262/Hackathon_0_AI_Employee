"""
Audit Logger - Gold Tier Component
===================================
Comprehensive logging for compliance and debugging.

Logs EVERYTHING the AI Employee does:
- All file operations
- All emails sent
- All social media posts
- All approvals/rejections
- All errors
- System health checks

This creates a complete audit trail for:
1. Debugging issues
2. Compliance (know what AI did)
3. Performance analysis
4. Security monitoring
"""

import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum
from functools import wraps


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    AUDIT = "AUDIT"  # Special level for audit events


class EventType(Enum):
    # File operations
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_MOVE = "file_move"

    # Communication
    EMAIL_DRAFT = "email_draft"
    EMAIL_SENT = "email_sent"
    EMAIL_RECEIVED = "email_received"

    # Social media
    SOCIAL_DRAFT = "social_draft"
    SOCIAL_POSTED = "social_posted"

    # Approvals
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"

    # Tasks
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # System
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    SYSTEM_ERROR = "system_error"
    HEALTH_CHECK = "health_check"

    # Security
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    SENSITIVE_ACCESS = "sensitive_access"


class AuditLogger:
    """
    Comprehensive audit logging system.
    Creates immutable, timestamped logs of all AI Employee actions.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_folder = self.vault_path / 'Logs'
        self.audit_folder = self.logs_folder / 'Audit'
        self.error_folder = self.logs_folder / 'Errors'
        self.daily_folder = self.logs_folder / 'Daily'

        # Create folders
        for folder in [self.audit_folder, self.error_folder, self.daily_folder]:
            folder.mkdir(parents=True, exist_ok=True)

        # Setup file logging
        self._setup_file_logging()

        # Session ID for this run
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        self.log(EventType.SYSTEM_START, {"session_id": self.session_id})

    def _setup_file_logging(self):
        """Setup Python logging to file."""
        log_file = self.logs_folder / f'system_{datetime.now().strftime("%Y%m%d")}.log'

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('AuditLogger')

    def log(self, event_type: EventType, data: Dict[str, Any],
            level: LogLevel = LogLevel.INFO, actor: str = "ai_employee") -> str:
        """
        Log an event with full audit trail.

        Returns:
            Event ID for reference
        """
        event_id = self._generate_event_id()
        timestamp = datetime.now().isoformat()

        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "session_id": self.session_id,
            "event_type": event_type.value,
            "level": level.value,
            "actor": actor,
            "data": data,
            "checksum": None  # Will be calculated
        }

        # Calculate checksum for integrity
        event["checksum"] = self._calculate_checksum(event)

        # Write to audit log
        self._write_audit_log(event)

        # Write to daily summary
        self._write_daily_log(event)

        # Handle errors specially
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self._write_error_log(event)

        # Log to Python logger
        log_message = f"[{event_type.value}] {json.dumps(data)}"
        if level == LogLevel.ERROR:
            self.logger.error(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        return event_id

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"EVT_{timestamp}"

    def _calculate_checksum(self, event: Dict) -> str:
        """Calculate checksum for event integrity verification."""
        # Remove checksum field for calculation
        event_copy = {k: v for k, v in event.items() if k != 'checksum'}
        event_str = json.dumps(event_copy, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()[:16]

    def _write_audit_log(self, event: Dict):
        """Write to immutable audit log."""
        date_str = datetime.now().strftime('%Y%m%d')
        audit_file = self.audit_folder / f'audit_{date_str}.jsonl'

        with open(audit_file, 'a') as f:
            f.write(json.dumps(event) + '\n')

    def _write_daily_log(self, event: Dict):
        """Write to human-readable daily log."""
        date_str = datetime.now().strftime('%Y%m%d')
        daily_file = self.daily_folder / f'daily_{date_str}.md'

        # Create header if new file
        if not daily_file.exists():
            header = f'''# Daily Activity Log - {datetime.now().strftime('%B %d, %Y')}

| Time | Event | Details |
|------|-------|---------|
'''
            daily_file.write_text(header)

        # Append event
        time_str = datetime.now().strftime('%H:%M:%S')
        event_type = event['event_type']
        details = str(event['data'])[:50] + '...' if len(str(event['data'])) > 50 else str(event['data'])

        with open(daily_file, 'a') as f:
            f.write(f"| {time_str} | {event_type} | {details} |\n")

    def _write_error_log(self, event: Dict):
        """Write to error log for quick debugging."""
        error_file = self.error_folder / f'errors_{datetime.now().strftime("%Y%m%d")}.json'

        errors = []
        if error_file.exists():
            with open(error_file, 'r') as f:
                errors = json.load(f)

        errors.append(event)

        with open(error_file, 'w') as f:
            json.dump(errors, f, indent=2)

    # Convenience methods for common events

    def log_email_sent(self, to: str, subject: str, success: bool):
        """Log email sent event."""
        self.log(
            EventType.EMAIL_SENT,
            {"to": to, "subject": subject, "success": success},
            LogLevel.INFO if success else LogLevel.ERROR
        )

    def log_approval(self, item: str, approved: bool, approver: str = "human"):
        """Log approval decision."""
        event_type = EventType.APPROVAL_GRANTED if approved else EventType.APPROVAL_DENIED
        self.log(event_type, {"item": item, "approver": approver})

    def log_task(self, task_id: str, status: str, details: Dict = None):
        """Log task status change."""
        event_map = {
            "created": EventType.TASK_CREATED,
            "started": EventType.TASK_STARTED,
            "completed": EventType.TASK_COMPLETED,
            "failed": EventType.TASK_FAILED
        }
        event_type = event_map.get(status, EventType.TASK_CREATED)
        self.log(event_type, {"task_id": task_id, "status": status, **(details or {})})

    def log_error(self, error: str, context: Dict = None):
        """Log error event."""
        self.log(
            EventType.SYSTEM_ERROR,
            {"error": error, **(context or {})},
            LogLevel.ERROR
        )

    def log_file_operation(self, operation: str, path: str, success: bool = True):
        """Log file operation."""
        event_map = {
            "read": EventType.FILE_READ,
            "write": EventType.FILE_WRITE,
            "delete": EventType.FILE_DELETE,
            "move": EventType.FILE_MOVE
        }
        event_type = event_map.get(operation, EventType.FILE_READ)
        self.log(event_type, {"path": path, "success": success})

    def get_daily_summary(self) -> Dict[str, Any]:
        """Get summary of today's activity."""
        date_str = datetime.now().strftime('%Y%m%d')
        audit_file = self.audit_folder / f'audit_{date_str}.jsonl'

        summary = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "total_events": 0,
            "by_type": {},
            "errors": 0
        }

        if audit_file.exists():
            with open(audit_file, 'r') as f:
                for line in f:
                    event = json.loads(line)
                    summary["total_events"] += 1
                    event_type = event["event_type"]
                    summary["by_type"][event_type] = summary["by_type"].get(event_type, 0) + 1
                    if event["level"] in ["ERROR", "CRITICAL"]:
                        summary["errors"] += 1

        return summary

    def verify_log_integrity(self, date_str: str = None) -> Dict[str, Any]:
        """Verify integrity of audit logs using checksums."""
        if not date_str:
            date_str = datetime.now().strftime('%Y%m%d')

        audit_file = self.audit_folder / f'audit_{date_str}.jsonl'

        result = {
            "date": date_str,
            "total_events": 0,
            "valid": 0,
            "invalid": 0,
            "integrity": "unknown"
        }

        if not audit_file.exists():
            result["integrity"] = "no_logs"
            return result

        with open(audit_file, 'r') as f:
            for line in f:
                event = json.loads(line)
                result["total_events"] += 1

                # Verify checksum
                stored_checksum = event.get("checksum")
                calculated_checksum = self._calculate_checksum(event)

                if stored_checksum == calculated_checksum:
                    result["valid"] += 1
                else:
                    result["invalid"] += 1

        result["integrity"] = "valid" if result["invalid"] == 0 else "compromised"
        return result


# Decorator for automatic logging
def audit_logged(event_type: EventType):
    """Decorator to automatically log function calls."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get logger from first argument if it's an object with audit_logger
            audit_logger = None
            if args and hasattr(args[0], 'audit_logger'):
                audit_logger = args[0].audit_logger

            try:
                result = func(*args, **kwargs)
                if audit_logger:
                    audit_logger.log(event_type, {
                        "function": func.__name__,
                        "success": True
                    })
                return result
            except Exception as e:
                if audit_logger:
                    audit_logger.log(event_type, {
                        "function": func.__name__,
                        "success": False,
                        "error": str(e)
                    }, LogLevel.ERROR)
                raise

        return wrapper
    return decorator


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python audit_logger.py <vault_path> [--summary] [--verify]")
        sys.exit(1)

    vault_path = sys.argv[1]
    logger = AuditLogger(vault_path)

    if '--summary' in sys.argv:
        summary = logger.get_daily_summary()
        print("\n📊 Daily Summary")
        print("=" * 40)
        print(f"Date: {summary['date']}")
        print(f"Total Events: {summary['total_events']}")
        print(f"Errors: {summary['errors']}")
        print("\nBy Type:")
        for event_type, count in summary['by_type'].items():
            print(f"  {event_type}: {count}")

    elif '--verify' in sys.argv:
        result = logger.verify_log_integrity()
        print("\n🔒 Log Integrity Check")
        print("=" * 40)
        print(f"Date: {result['date']}")
        print(f"Total Events: {result['total_events']}")
        print(f"Valid: {result['valid']}")
        print(f"Invalid: {result['invalid']}")
        print(f"Integrity: {result['integrity']}")

    else:
        # Test logging
        logger.log(EventType.SYSTEM_START, {"test": True})
        logger.log_email_sent("test@example.com", "Test Subject", True)
        logger.log_task("TASK_001", "created", {"type": "email"})
        print("✅ Test logs created")
        print(f"   Check: {logger.audit_folder}")
