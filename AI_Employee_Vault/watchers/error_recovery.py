"""
Error Recovery & Graceful Degradation - Gold Tier Component
============================================================
Handles errors gracefully so the AI Employee doesn't crash.

Principles:
1. Never crash completely - keep other tasks running
2. Retry with exponential backoff
3. Fallback to simpler methods
4. Alert human when stuck
5. Self-heal when possible
"""

import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Callable, Optional
from functools import wraps
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ErrorRecovery')


class RecoveryStrategy(Enum):
    RETRY = "retry"              # Try again
    FALLBACK = "fallback"        # Use simpler method
    SKIP = "skip"                # Skip and continue
    ALERT = "alert"              # Alert human
    QUARANTINE = "quarantine"    # Isolate problematic item


class ErrorRecovery:
    """
    Central error recovery system for AI Employee.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.quarantine_folder = self.vault_path / 'Quarantine'
        self.alerts_folder = self.vault_path / 'Needs_Action' / 'Alerts'
        self.error_log = self.vault_path / 'Logs' / 'Errors'

        for folder in [self.quarantine_folder, self.alerts_folder, self.error_log]:
            folder.mkdir(parents=True, exist_ok=True)

        # Error counts for circuit breaker
        self.error_counts: Dict[str, int] = {}
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_reset = timedelta(minutes=15)
        self.last_error_time: Dict[str, datetime] = {}

        # Fallback handlers
        self.fallbacks: Dict[str, Callable] = {}

        logger.info("Error Recovery system initialized")

    def register_fallback(self, operation: str, fallback_fn: Callable):
        """Register a fallback function for an operation."""
        self.fallbacks[operation] = fallback_fn

    def handle_error(self, error: Exception, context: Dict[str, Any],
                     strategy: RecoveryStrategy = RecoveryStrategy.RETRY) -> Dict[str, Any]:
        """
        Handle an error with the specified recovery strategy.
        """
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        operation = context.get('operation', 'unknown')

        result = {
            "error_id": error_id,
            "error": str(error),
            "strategy": strategy.value,
            "recovered": False,
            "timestamp": datetime.now().isoformat()
        }

        # Log the error
        self._log_error(error_id, error, context)

        # Update error count for circuit breaker
        self._update_error_count(operation)

        # Check circuit breaker
        if self._is_circuit_open(operation):
            logger.warning(f"Circuit breaker OPEN for {operation}")
            result["strategy"] = RecoveryStrategy.ALERT.value
            self._create_alert(error_id, error, context, "Circuit breaker triggered")
            return result

        # Apply recovery strategy
        if strategy == RecoveryStrategy.RETRY:
            result = self._handle_retry(error, context, result)

        elif strategy == RecoveryStrategy.FALLBACK:
            result = self._handle_fallback(error, context, result)

        elif strategy == RecoveryStrategy.SKIP:
            result = self._handle_skip(error, context, result)

        elif strategy == RecoveryStrategy.ALERT:
            result = self._handle_alert(error, context, result)

        elif strategy == RecoveryStrategy.QUARANTINE:
            result = self._handle_quarantine(error, context, result)

        return result

    def _handle_retry(self, error: Exception, context: Dict,
                      result: Dict) -> Dict[str, Any]:
        """Retry with exponential backoff."""
        max_retries = context.get('max_retries', 3)
        retry_fn = context.get('retry_fn')
        retry_args = context.get('retry_args', {})

        if not retry_fn:
            result["message"] = "No retry function provided"
            return result

        for attempt in range(max_retries):
            delay = (2 ** attempt) * 1  # Exponential backoff: 1, 2, 4 seconds
            logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s")
            time.sleep(delay)

            try:
                retry_result = retry_fn(**retry_args)
                result["recovered"] = True
                result["retry_attempts"] = attempt + 1
                result["retry_result"] = retry_result
                logger.info(f"Recovered after {attempt + 1} retries")
                return result
            except Exception as e:
                logger.warning(f"Retry {attempt + 1} failed: {e}")

        result["message"] = f"All {max_retries} retries failed"
        return result

    def _handle_fallback(self, error: Exception, context: Dict,
                         result: Dict) -> Dict[str, Any]:
        """Use fallback method."""
        operation = context.get('operation', 'unknown')

        if operation in self.fallbacks:
            try:
                fallback_result = self.fallbacks[operation](context)
                result["recovered"] = True
                result["fallback_result"] = fallback_result
                logger.info(f"Fallback successful for {operation}")
            except Exception as e:
                result["message"] = f"Fallback also failed: {e}"
        else:
            result["message"] = f"No fallback registered for {operation}"

        return result

    def _handle_skip(self, error: Exception, context: Dict,
                     result: Dict) -> Dict[str, Any]:
        """Skip the problematic item and continue."""
        result["recovered"] = True
        result["message"] = "Skipped problematic item"

        # Move item to a skipped folder if applicable
        if 'file_path' in context:
            skipped_folder = self.vault_path / 'Skipped'
            skipped_folder.mkdir(exist_ok=True)

            file_path = Path(context['file_path'])
            if file_path.exists():
                dest = skipped_folder / file_path.name
                file_path.rename(dest)
                result["skipped_to"] = str(dest)

        return result

    def _handle_alert(self, error: Exception, context: Dict,
                      result: Dict) -> Dict[str, Any]:
        """Alert human about the error."""
        error_id = result['error_id']
        self._create_alert(error_id, error, context)
        result["message"] = "Human alerted"
        return result

    def _handle_quarantine(self, error: Exception, context: Dict,
                           result: Dict) -> Dict[str, Any]:
        """Quarantine problematic item for manual review."""
        if 'file_path' in context:
            file_path = Path(context['file_path'])
            if file_path.exists():
                dest = self.quarantine_folder / file_path.name
                file_path.rename(dest)
                result["quarantined_to"] = str(dest)
                result["message"] = "Item quarantined for manual review"

        # Create quarantine notice
        notice_file = self.quarantine_folder / f'NOTICE_{result["error_id"]}.md'
        notice_content = f'''---
type: quarantine_notice
error_id: {result['error_id']}
created: {datetime.now().isoformat()}
---

# Quarantined Item

## Error
{str(error)}

## Context
{json.dumps(context, indent=2, default=str)}

## Action Required
Please review the quarantined item and either:
- Fix and move back to /Needs_Action
- Delete if not needed

---
*Quarantined by Error Recovery System*
'''
        notice_file.write_text(notice_content)

        return result

    def _create_alert(self, error_id: str, error: Exception,
                      context: Dict, reason: str = None):
        """Create alert for human attention."""
        alert_file = self.alerts_folder / f'ALERT_{error_id}.md'

        content = f'''---
type: error_alert
error_id: {error_id}
priority: high
created: {datetime.now().isoformat()}
status: pending
---

# ⚠️ Error Alert - Human Attention Required

## Error ID
`{error_id}`

## Error Message
```
{str(error)}
```

## Reason
{reason or 'Error requires human intervention'}

## Context
```json
{json.dumps(context, indent=2, default=str)}
```

## Suggested Actions
- [ ] Review the error details
- [ ] Check related logs in /Logs/Errors
- [ ] Fix the underlying issue
- [ ] Retry the operation if safe

---

*Alert generated by Error Recovery System*
*Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
'''
        alert_file.write_text(content)
        logger.info(f"Alert created: {alert_file}")

    def _log_error(self, error_id: str, error: Exception, context: Dict):
        """Log error to file."""
        log_file = self.error_log / f'errors_{datetime.now().strftime("%Y%m%d")}.json'

        errors = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                errors = json.load(f)

        errors.append({
            "error_id": error_id,
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context,
            "timestamp": datetime.now().isoformat()
        })

        with open(log_file, 'w') as f:
            json.dump(errors, f, indent=2)

    def _update_error_count(self, operation: str):
        """Update error count for circuit breaker."""
        now = datetime.now()

        # Reset count if enough time has passed
        if operation in self.last_error_time:
            if now - self.last_error_time[operation] > self.circuit_breaker_reset:
                self.error_counts[operation] = 0

        self.error_counts[operation] = self.error_counts.get(operation, 0) + 1
        self.last_error_time[operation] = now

    def _is_circuit_open(self, operation: str) -> bool:
        """Check if circuit breaker is open (too many errors)."""
        return self.error_counts.get(operation, 0) >= self.circuit_breaker_threshold

    def reset_circuit(self, operation: str):
        """Manually reset circuit breaker for an operation."""
        self.error_counts[operation] = 0
        logger.info(f"Circuit breaker reset for {operation}")


def with_recovery(strategy: RecoveryStrategy = RecoveryStrategy.RETRY,
                  max_retries: int = 3):
    """Decorator to add error recovery to functions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Try to get recovery system from first arg
                recovery = None
                if args and hasattr(args[0], 'error_recovery'):
                    recovery = args[0].error_recovery

                if recovery:
                    context = {
                        'operation': func.__name__,
                        'args': str(args)[:100],
                        'kwargs': str(kwargs)[:100],
                        'max_retries': max_retries,
                        'retry_fn': func,
                        'retry_args': kwargs
                    }
                    result = recovery.handle_error(e, context, strategy)

                    if result.get('recovered'):
                        return result.get('retry_result') or result.get('fallback_result')

                raise

        return wrapper
    return decorator


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python error_recovery.py <vault_path>")
        sys.exit(1)

    vault_path = sys.argv[1]
    recovery = ErrorRecovery(vault_path)

    # Test error handling
    print("Testing Error Recovery System")
    print("=" * 40)

    # Simulate an error
    try:
        raise ValueError("Test error for demonstration")
    except Exception as e:
        result = recovery.handle_error(
            e,
            {'operation': 'test', 'file_path': None},
            RecoveryStrategy.ALERT
        )
        print(f"Result: {json.dumps(result, indent=2)}")

    print("\n✅ Error recovery test complete")
    print(f"   Check alerts: {recovery.alerts_folder}")
