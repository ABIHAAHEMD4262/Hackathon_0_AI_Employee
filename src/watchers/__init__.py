"""
AI Employee Watchers Package
============================
All perception modules (watchers) for the AI Employee system.
"""

from .base_watcher import BaseWatcher, WatcherStatus
from .gmail_watcher import GmailWatcher
from .whatsapp_watcher import WhatsAppWatcher
from .calendar_watcher import CalendarWatcher
from .slack_watcher import SlackWatcher
from .discord_watcher import DiscordWatcher
from .filesystem_watcher import FileSystemWatcher
from .twitter_watcher import TwitterWatcher
from .linkedin_watcher import LinkedInWatcher
from .sms_watcher import SMSWatcher

__all__ = [
    'BaseWatcher',
    'WatcherStatus',
    'GmailWatcher',
    'WhatsAppWatcher',
    'CalendarWatcher',
    'SlackWatcher',
    'DiscordWatcher',
    'FileSystemWatcher',
    'TwitterWatcher',
    'LinkedInWatcher',
    'SMSWatcher',
]
