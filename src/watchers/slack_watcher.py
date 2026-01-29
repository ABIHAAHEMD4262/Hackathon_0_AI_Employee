"""
Slack Watcher Module
====================
Monitors Slack for messages, mentions, and DMs.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import os

from .base_watcher import BaseWatcher, Event, EventType, generate_event_id, RateLimiter


class SlackWatcher(BaseWatcher):
    """
    Slack message and mention watcher.

    Features:
    - Direct message monitoring
    - Channel mention detection
    - Thread reply tracking
    - Reaction monitoring
    - Integration with Slack Web API

    Requires:
    - SLACK_BOT_TOKEN environment variable
    - pip install slack-sdk
    """

    def __init__(
        self,
        check_interval: int = 15,
        config: Optional[Dict] = None,
        channels: List[str] = None
    ):
        super().__init__("Slack", check_interval, config)
        self.bot_token = os.getenv("SLACK_BOT_TOKEN") or config.get("bot_token") if config else None
        self.channels = channels or []
        self.client = None
        self.bot_user_id: Optional[str] = None

        # Track seen messages
        self.last_message_ts: Dict[str, str] = {}

        # Rate limiting (Slack allows ~50 requests/minute)
        self.rate_limiter = RateLimiter(max_calls=40, period_seconds=60)

        # Priority channels/users
        self.priority_channels: List[str] = config.get("priority_channels", []) if config else []
        self.vip_users: List[str] = config.get("vip_users", []) if config else []

    async def setup(self) -> bool:
        """Initialize Slack client."""
        try:
            from slack_sdk import WebClient
            from slack_sdk.errors import SlackApiError

            if not self.bot_token:
                self.logger.warning("SLACK_BOT_TOKEN not set. Slack watcher inactive.")
                return True

            self.client = WebClient(token=self.bot_token)

            # Test connection and get bot info
            response = self.client.auth_test()
            self.bot_user_id = response['user_id']
            self.logger.info(f"Slack connected as {response['user']}")

            # Get channels to monitor
            if not self.channels:
                channels_response = self.client.conversations_list(
                    types="public_channel,private_channel,im"
                )
                self.channels = [c['id'] for c in channels_response['channels'][:10]]

            return True

        except ImportError:
            self.logger.warning("slack-sdk not installed. Run: pip install slack-sdk")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Slack: {e}")
            return False

    async def check(self) -> List[Event]:
        """Check for new Slack messages."""
        events = []

        if not self.client:
            return events

        try:
            # Check each channel
            for channel_id in self.channels:
                channel_events = await self._check_channel(channel_id)
                events.extend(channel_events)

        except Exception as e:
            self.logger.error(f"Error checking Slack: {e}")

        return events

    async def _check_channel(self, channel_id: str) -> List[Event]:
        """Check a specific channel for new messages."""
        events = []

        try:
            await self.rate_limiter.acquire()

            # Get channel info
            try:
                channel_info = self.client.conversations_info(channel=channel_id)
                channel_name = channel_info['channel'].get('name', channel_id)
                is_dm = channel_info['channel'].get('is_im', False)
            except Exception:
                channel_name = channel_id
                is_dm = False

            # Get messages
            oldest = self.last_message_ts.get(channel_id, '0')
            response = self.client.conversations_history(
                channel=channel_id,
                oldest=oldest,
                limit=20
            )

            messages = response.get('messages', [])

            for msg in reversed(messages):  # Process oldest first
                # Skip bot's own messages
                if msg.get('user') == self.bot_user_id:
                    continue

                # Skip already processed
                if msg.get('ts', '0') <= oldest:
                    continue

                event = await self._create_message_event(msg, channel_id, channel_name, is_dm)
                if event:
                    events.append(event)

                # Update last seen
                self.last_message_ts[channel_id] = msg.get('ts', oldest)

        except Exception as e:
            self.logger.debug(f"Error checking channel {channel_id}: {e}")

        return events

    async def _create_message_event(
        self,
        msg: Dict,
        channel_id: str,
        channel_name: str,
        is_dm: bool
    ) -> Optional[Event]:
        """Create an Event from a Slack message."""
        try:
            user_id = msg.get('user', 'unknown')
            text = msg.get('text', '')

            # Get user info
            user_name = user_id
            try:
                await self.rate_limiter.acquire()
                user_info = self.client.users_info(user=user_id)
                user_name = user_info['user'].get('real_name', user_info['user'].get('name', user_id))
            except Exception:
                pass

            # Check if mentioned
            is_mention = self.bot_user_id and f"<@{self.bot_user_id}>" in text

            # Determine priority
            priority = 5
            if is_dm:
                priority = 2
            elif is_mention:
                priority = 3
            elif channel_name in self.priority_channels:
                priority = 3
            elif user_id in self.vip_users:
                priority = 2

            # Check for urgency keywords
            text_lower = text.lower()
            if any(word in text_lower for word in ['urgent', 'asap', 'help', 'emergency']):
                priority = min(priority, 2)

            return Event(
                id=generate_event_id("slack", msg.get('ts', '')),
                type=EventType.SLACK_MESSAGE,
                source="slack",
                channel="slack",
                timestamp=datetime.fromtimestamp(float(msg.get('ts', 0))),
                data={
                    "message_ts": msg.get('ts'),
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "user_id": user_id,
                    "user_name": user_name,
                    "text": text,
                    "is_dm": is_dm,
                    "is_mention": is_mention,
                    "thread_ts": msg.get('thread_ts'),
                    "attachments": msg.get('attachments', []),
                    "files": [f.get('name') for f in msg.get('files', [])]
                },
                priority=priority
            )

        except Exception as e:
            self.logger.error(f"Error creating Slack event: {e}")
            return None

    async def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None
    ) -> bool:
        """Send a Slack message (requires HITL approval)."""
        if not self.client:
            return False

        try:
            await self.rate_limiter.acquire()
            self.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to send Slack message: {e}")
            return False

    async def add_reaction(self, channel: str, timestamp: str, emoji: str) -> bool:
        """Add a reaction to a message."""
        if not self.client:
            return False

        try:
            await self.rate_limiter.acquire()
            self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to add reaction: {e}")
            return False

    async def teardown(self):
        """Clean up Slack resources."""
        self.client = None
