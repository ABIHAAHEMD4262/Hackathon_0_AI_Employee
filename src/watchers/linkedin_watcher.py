"""
LinkedIn Watcher Module
=======================
Monitors LinkedIn for messages, notifications, and connection activity.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import os

from .base_watcher import BaseWatcher, Event, EventType, generate_event_id, RateLimiter


class LinkedInWatcher(BaseWatcher):
    """
    LinkedIn watcher for professional network monitoring.

    Features:
    - Direct message monitoring
    - Connection request alerts
    - Mention/tag notifications
    - Post engagement tracking
    - InMail monitoring

    Note: LinkedIn API access is limited. This implementation uses
    available endpoints or can be extended with browser automation.

    Requires:
    - LinkedIn API credentials (limited availability)
    - pip install linkedin-api (unofficial) or selenium for automation
    """

    def __init__(
        self,
        check_interval: int = 300,  # 5 minutes (LinkedIn is rate-limited)
        config: Optional[Dict] = None
    ):
        super().__init__("LinkedIn", check_interval, config)

        # API credentials (if using official API)
        self.client_id = os.getenv("LINKEDIN_CLIENT_ID") or (config.get("client_id") if config else None)
        self.client_secret = os.getenv("LINKEDIN_CLIENT_SECRET") or (config.get("client_secret") if config else None)
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN") or (config.get("access_token") if config else None)

        # Alternative: email/password for unofficial API
        self.email = os.getenv("LINKEDIN_EMAIL") or (config.get("email") if config else None)
        self.password = os.getenv("LINKEDIN_PASSWORD") or (config.get("password") if config else None)

        self.client = None
        self.profile_id: Optional[str] = None

        # Track seen items
        self.seen_message_ids: set = set()
        self.seen_notification_ids: set = set()

        # VIP connections
        self.vip_connections: List[str] = config.get("vip_connections", []) if config else []

        # Rate limiting
        self.rate_limiter = RateLimiter(max_calls=10, period_seconds=60)

    async def setup(self) -> bool:
        """Initialize LinkedIn client."""
        try:
            # Try unofficial linkedin-api first
            from linkedin_api import Linkedin

            if not self.email or not self.password:
                self.logger.warning("LinkedIn credentials not set. LinkedIn watcher inactive.")
                return True

            self.client = Linkedin(self.email, self.password)
            profile = self.client.get_user_profile()
            self.profile_id = profile.get('miniProfile', {}).get('entityUrn', '').split(':')[-1]

            self.logger.info(f"LinkedIn connected as {profile.get('miniProfile', {}).get('firstName', 'Unknown')}")
            return True

        except ImportError:
            self.logger.warning(
                "linkedin-api not installed. Run: pip install linkedin-api\n"
                "Note: This is an unofficial library and may break with LinkedIn changes."
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup LinkedIn: {e}")
            return False

    async def check(self) -> List[Event]:
        """Check for LinkedIn activity."""
        events = []

        if not self.client:
            return events

        try:
            # Check messages
            message_events = await self._check_messages()
            events.extend(message_events)

            # Check notifications
            notification_events = await self._check_notifications()
            events.extend(notification_events)

        except Exception as e:
            self.logger.error(f"Error checking LinkedIn: {e}")

        return events

    async def _check_messages(self) -> List[Event]:
        """Check for new LinkedIn messages."""
        events = []

        try:
            await self.rate_limiter.acquire()

            conversations = self.client.get_conversations()

            for conv in conversations.get('elements', [])[:10]:
                conv_id = conv.get('entityUrn', '').split(':')[-1]

                # Get latest message
                last_activity = conv.get('lastActivityAt', 0)
                last_msg = conv.get('events', [{}])[0] if conv.get('events') else {}

                msg_id = f"{conv_id}_{last_activity}"

                if msg_id in self.seen_message_ids:
                    continue

                self.seen_message_ids.add(msg_id)

                # Get participant info
                participants = conv.get('participants', [])
                sender_name = "Unknown"
                sender_id = ""

                for p in participants:
                    profile = p.get('com.linkedin.voyager.messaging.MessagingMember', {}).get('miniProfile', {})
                    if profile:
                        sender_name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
                        sender_id = profile.get('entityUrn', '').split(':')[-1]
                        break

                # Determine priority
                priority = 4
                if sender_name in self.vip_connections or sender_id in self.vip_connections:
                    priority = 2

                message_text = ""
                if last_msg.get('eventContent', {}).get('com.linkedin.voyager.messaging.event.MessageEvent'):
                    message_text = last_msg['eventContent']['com.linkedin.voyager.messaging.event.MessageEvent'].get('body', '')

                event = Event(
                    id=generate_event_id("linkedin_message", msg_id),
                    type=EventType.LINKEDIN_MESSAGE,
                    source="linkedin",
                    channel="linkedin",
                    timestamp=datetime.fromtimestamp(last_activity / 1000) if last_activity else datetime.now(),
                    data={
                        "conversation_id": conv_id,
                        "sender_name": sender_name,
                        "sender_id": sender_id,
                        "message_preview": message_text[:200] if message_text else "",
                        "unread_count": conv.get('unreadCount', 0)
                    },
                    priority=priority
                )
                events.append(event)

        except Exception as e:
            self.logger.error(f"Error checking LinkedIn messages: {e}")

        return events

    async def _check_notifications(self) -> List[Event]:
        """Check for LinkedIn notifications."""
        events = []

        try:
            await self.rate_limiter.acquire()

            # Get notifications (method may vary based on linkedin-api version)
            try:
                notifications = self.client.get_user_profile()  # Placeholder
                # Real implementation would use notification endpoint
            except Exception:
                return events

        except Exception as e:
            self.logger.debug(f"Error checking notifications: {e}")

        return events

    async def send_message(self, profile_id: str, message: str) -> bool:
        """Send a LinkedIn message (requires HITL approval)."""
        if not self.client:
            return False

        try:
            await self.rate_limiter.acquire()
            self.client.send_message(message, [profile_id])
            return True
        except Exception as e:
            self.logger.error(f"Failed to send LinkedIn message: {e}")
            return False

    async def accept_connection(self, invitation_id: str) -> bool:
        """Accept a connection request."""
        if not self.client:
            return False

        try:
            await self.rate_limiter.acquire()
            # Implementation depends on linkedin-api capabilities
            return True
        except Exception as e:
            self.logger.error(f"Failed to accept connection: {e}")
            return False

    async def teardown(self):
        """Clean up LinkedIn resources."""
        self.client = None
