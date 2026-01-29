"""
Base Watcher Template
All specific watchers (Gmail, LinkedIn, etc.) inherit from this base class
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any


class BaseWatcher(ABC):
    """
    Abstract base class for all watcher implementations.
    Provides common functionality for monitoring and creating action files.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the watcher

        Args:
            vault_path: Path to the Obsidian vault
            check_interval: Seconds between checks (default 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = self._setup_logging()
        self.processed_ids = set()  # Track what we've already processed

        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for this watcher"""
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # File handler
        log_dir = self.vault_path / 'Logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f'{self.__class__.__name__.lower()}.log'
        )
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check the monitored source for new items

        Returns:
            List of new items to process (implementation-specific format)
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create a markdown file in Needs_Action folder

        Args:
            item: The item to create an action file for

        Returns:
            Path to the created file
        """
        pass

    def generate_frontmatter(self, data: Dict[str, Any]) -> str:
        """
        Generate YAML frontmatter for markdown files

        Args:
            data: Dictionary of frontmatter key-value pairs

        Returns:
            Formatted frontmatter string
        """
        frontmatter = "---\n"
        for key, value in data.items():
            frontmatter += f"{key}: {value}\n"
        frontmatter += "---\n\n"
        return frontmatter

    def sanitize_filename(self, text: str, max_length: int = 50) -> str:
        """
        Create a safe filename from text

        Args:
            text: Input text
            max_length: Maximum filename length

        Returns:
            Sanitized filename
        """
        # Remove special characters
        safe = "".join(c for c in text if c.isalnum() or c in (' ', '-', '_'))
        # Replace spaces with underscores
        safe = safe.replace(' ', '_')
        # Truncate if too long
        if len(safe) > max_length:
            safe = safe[:max_length]
        return safe

    def mark_processed(self, item_id: str):
        """Mark an item as processed to avoid duplicates"""
        self.processed_ids.add(item_id)

    def is_processed(self, item_id: str) -> bool:
        """Check if an item has already been processed"""
        return item_id in self.processed_ids

    def run(self):
        """
        Main loop - continuously monitor and process new items
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Monitoring with {self.check_interval}s interval')
        self.logger.info(f'Vault path: {self.vault_path}')

        while True:
            try:
                # Check for new items
                items = self.check_for_updates()

                if items:
                    self.logger.info(f'Found {len(items)} new item(s)')

                    # Process each item
                    for item in items:
                        try:
                            filepath = self.create_action_file(item)
                            self.logger.info(f'Created action file: {filepath.name}')
                        except Exception as e:
                            self.logger.error(f'Error creating action file: {e}')

                # Wait before next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                self.logger.info('Received shutdown signal')
                break
            except Exception as e:
                self.logger.error(f'Error in main loop: {e}')
                # Wait a bit before retrying to avoid rapid failure loops
                time.sleep(self.check_interval)

        self.logger.info(f'Stopped {self.__class__.__name__}')

    def run_once(self):
        """
        Run a single check cycle (useful for testing)
        """
        self.logger.info(f'Running single check cycle for {self.__class__.__name__}')

        try:
            items = self.check_for_updates()

            if items:
                self.logger.info(f'Found {len(items)} item(s)')

                for item in items:
                    filepath = self.create_action_file(item)
                    self.logger.info(f'Created: {filepath.name}')
            else:
                self.logger.info('No new items found')

        except Exception as e:
            self.logger.error(f'Error during check: {e}')
            raise
