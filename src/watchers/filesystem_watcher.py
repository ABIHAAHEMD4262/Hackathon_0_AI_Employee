"""
FileSystem Watcher Module
=========================
Monitors directories for file changes, new files, and document processing.
"""

import asyncio
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import hashlib
import json

from .base_watcher import BaseWatcher, Event, EventType, generate_event_id


class FileSystemWatcher(BaseWatcher):
    """
    File system watcher for document and file monitoring.

    Features:
    - New file detection
    - File modification tracking
    - File deletion detection
    - Invoice/document type detection
    - Automatic categorization
    """

    def __init__(
        self,
        watch_paths: List[str] = None,
        check_interval: int = 30,
        config: Optional[Dict] = None
    ):
        super().__init__("FileSystem", check_interval, config)
        self.watch_paths = [Path(p) for p in (watch_paths or ["nerve_center/inbox"])]

        # Track file states
        self.file_states: Dict[str, Dict] = {}
        self.seen_files: Set[str] = set()

        # File type patterns for categorization
        self.invoice_patterns = ['invoice', 'bill', 'receipt', 'statement', 'payment']
        self.contract_patterns = ['contract', 'agreement', 'nda', 'terms']
        self.report_patterns = ['report', 'summary', 'analysis', 'review']

        # Supported file types
        self.document_extensions = {'.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'}
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
        self.data_extensions = {'.csv', '.xlsx', '.xls', '.json', '.xml'}

    async def setup(self) -> bool:
        """Initialize file system monitoring."""
        try:
            # Ensure watch paths exist
            for path in self.watch_paths:
                path.mkdir(parents=True, exist_ok=True)

            # Initial scan
            await self._initial_scan()

            self.logger.info(f"Watching paths: {[str(p) for p in self.watch_paths]}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup FileSystem watcher: {e}")
            return False

    async def _initial_scan(self):
        """Scan existing files to avoid processing as new."""
        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue

            for file_path in watch_path.rglob('*'):
                if file_path.is_file():
                    file_key = str(file_path)
                    self.seen_files.add(file_key)
                    self.file_states[file_key] = {
                        'mtime': file_path.stat().st_mtime,
                        'size': file_path.stat().st_size,
                        'hash': await self._get_file_hash(file_path)
                    }

    async def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file for change detection."""
        try:
            # Only hash first 1MB for large files
            with open(file_path, 'rb') as f:
                content = f.read(1024 * 1024)
                return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    async def check(self) -> List[Event]:
        """Check for file system changes."""
        events = []

        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue

            # Get current files
            current_files: Set[str] = set()

            for file_path in watch_path.rglob('*'):
                if not file_path.is_file():
                    continue

                file_key = str(file_path)
                current_files.add(file_key)

                try:
                    stat = file_path.stat()

                    if file_key not in self.seen_files:
                        # New file
                        event = await self._create_file_event(
                            file_path, EventType.FILE_CREATED
                        )
                        events.append(event)
                        self.seen_files.add(file_key)
                        self.file_states[file_key] = {
                            'mtime': stat.st_mtime,
                            'size': stat.st_size,
                            'hash': await self._get_file_hash(file_path)
                        }

                    elif file_key in self.file_states:
                        # Check for modifications
                        old_state = self.file_states[file_key]
                        if stat.st_mtime != old_state['mtime']:
                            new_hash = await self._get_file_hash(file_path)
                            if new_hash != old_state['hash']:
                                event = await self._create_file_event(
                                    file_path, EventType.FILE_MODIFIED
                                )
                                events.append(event)
                                self.file_states[file_key] = {
                                    'mtime': stat.st_mtime,
                                    'size': stat.st_size,
                                    'hash': new_hash
                                }

                except Exception as e:
                    self.logger.debug(f"Error checking file {file_path}: {e}")

            # Check for deleted files
            deleted_files = self.seen_files - current_files
            for file_key in deleted_files:
                if any(file_key.startswith(str(wp)) for wp in self.watch_paths):
                    event = Event(
                        id=generate_event_id("file_deleted", file_key),
                        type=EventType.FILE_DELETED,
                        source="filesystem",
                        channel="filesystem",
                        timestamp=datetime.now(),
                        data={
                            "filepath": file_key,
                            "filename": Path(file_key).name
                        },
                        priority=6
                    )
                    events.append(event)
                    self.seen_files.discard(file_key)
                    self.file_states.pop(file_key, None)

        return events

    async def _create_file_event(self, file_path: Path, event_type: EventType) -> Event:
        """Create an Event from a file."""
        stat = file_path.stat()
        filename = file_path.name.lower()
        extension = file_path.suffix.lower()

        # Detect file category
        category = self._categorize_file(filename, extension)

        # Determine if it's an invoice
        is_invoice = any(pattern in filename for pattern in self.invoice_patterns)

        # Determine priority
        priority = 5
        if is_invoice:
            priority = 2
            event_type = EventType.INVOICE_DETECTED
        elif category == 'contract':
            priority = 3
        elif category == 'report':
            priority = 4

        # Get mime type
        mime_type, _ = mimetypes.guess_type(str(file_path))

        return Event(
            id=generate_event_id("file", str(file_path)),
            type=event_type,
            source="filesystem",
            channel="filesystem",
            timestamp=datetime.now(),
            data={
                "filepath": str(file_path),
                "filename": file_path.name,
                "extension": extension,
                "size_bytes": stat.st_size,
                "size_human": self._human_readable_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "category": category,
                "is_invoice": is_invoice,
                "mime_type": mime_type,
                "parent_folder": file_path.parent.name
            },
            priority=priority,
            requires_approval=is_invoice  # Invoices need approval to process
        )

    def _categorize_file(self, filename: str, extension: str) -> str:
        """Categorize file based on name and extension."""
        if any(p in filename for p in self.invoice_patterns):
            return 'invoice'
        elif any(p in filename for p in self.contract_patterns):
            return 'contract'
        elif any(p in filename for p in self.report_patterns):
            return 'report'
        elif extension in self.document_extensions:
            return 'document'
        elif extension in self.image_extensions:
            return 'image'
        elif extension in self.data_extensions:
            return 'data'
        else:
            return 'other'

    def _human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    async def move_to_processed(self, filepath: str) -> bool:
        """Move a file to the processed folder."""
        try:
            source = Path(filepath)
            if not source.exists():
                return False

            # Find the processed folder relative to the source
            for watch_path in self.watch_paths:
                if str(source).startswith(str(watch_path)):
                    processed_path = watch_path.parent / "processed" / datetime.now().strftime("%Y-%m")
                    processed_path.mkdir(parents=True, exist_ok=True)

                    dest = processed_path / source.name
                    source.rename(dest)

                    # Update tracking
                    self.seen_files.discard(str(source))
                    self.file_states.pop(str(source), None)

                    return True

            return False
        except Exception as e:
            self.logger.error(f"Failed to move file: {e}")
            return False

    async def teardown(self):
        """Clean up file system watcher."""
        self.file_states.clear()
        self.seen_files.clear()
