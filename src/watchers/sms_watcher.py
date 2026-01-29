"""
SMS Watcher Module
==================
Monitors SMS messages via Twilio or similar service.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import os

from .base_watcher import BaseWatcher, Event, EventType, generate_event_id, RateLimiter


class SMSWatcher(BaseWatcher):
    """
    SMS watcher using Twilio API.

    Features:
    - Incoming SMS detection
    - MMS/media message support
    - VIP number prioritization
    - Keyword detection
    - Auto-response drafting

    Requires:
    - Twilio account and phone number
    - pip install twilio
    """

    def __init__(
        self,
        check_interval: int = 30,
        config: Optional[Dict] = None
    ):
        super().__init__("SMS", check_interval, config)

        # Twilio credentials
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID") or (config.get("account_sid") if config else None)
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN") or (config.get("auth_token") if config else None)
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER") or (config.get("phone_number") if config else None)

        self.client = None

        # Track seen messages
        self.seen_message_sids: set = set()
        self.last_check_time: Optional[datetime] = None

        # VIP phone numbers
        self.vip_numbers: List[str] = config.get("vip_numbers", []) if config else []

        # Urgency keywords
        self.urgent_keywords = ['urgent', 'emergency', 'asap', 'help', '911', 'call me']

        # Rate limiting
        self.rate_limiter = RateLimiter(max_calls=30, period_seconds=60)

    async def setup(self) -> bool:
        """Initialize Twilio client."""
        try:
            from twilio.rest import Client

            if not all([self.account_sid, self.auth_token]):
                self.logger.warning("Twilio credentials not set. SMS watcher inactive.")
                return True

            self.client = Client(self.account_sid, self.auth_token)

            # Verify credentials
            account = self.client.api.accounts(self.account_sid).fetch()
            self.logger.info(f"Twilio connected: {account.friendly_name}")

            self.last_check_time = datetime.utcnow() - timedelta(hours=1)
            return True

        except ImportError:
            self.logger.warning("twilio not installed. Run: pip install twilio")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup SMS watcher: {e}")
            return False

    async def check(self) -> List[Event]:
        """Check for new SMS messages."""
        events = []

        if not self.client:
            return events

        try:
            await self.rate_limiter.acquire()

            # Get messages received since last check
            messages = self.client.messages.list(
                to=self.phone_number,
                date_sent_after=self.last_check_time,
                limit=50
            )

            for msg in messages:
                if msg.sid in self.seen_message_sids:
                    continue

                # Only process inbound messages
                if msg.direction != 'inbound':
                    continue

                self.seen_message_sids.add(msg.sid)

                event = self._create_sms_event(msg)
                events.append(event)

            self.last_check_time = datetime.utcnow()

            # Cleanup old seen SIDs (keep last 500)
            if len(self.seen_message_sids) > 500:
                self.seen_message_sids = set(list(self.seen_message_sids)[-250:])

        except Exception as e:
            self.logger.error(f"Error checking SMS: {e}")

        return events

    def _create_sms_event(self, msg) -> Event:
        """Create an Event from an SMS message."""
        sender = msg.from_
        body = msg.body or ""

        # Normalize phone number
        sender_clean = self._normalize_phone(sender)

        # Determine priority
        priority = 4
        body_lower = body.lower()

        # VIP check
        if any(self._normalize_phone(vip) == sender_clean for vip in self.vip_numbers):
            priority = 1

        # Urgency check
        elif any(kw in body_lower for kw in self.urgent_keywords):
            priority = 2

        # Check for media (MMS)
        has_media = msg.num_media and int(msg.num_media) > 0

        return Event(
            id=generate_event_id("sms", msg.sid),
            type=EventType.SMS_RECEIVED,
            source="sms",
            channel="sms",
            timestamp=msg.date_sent or datetime.now(),
            data={
                "sid": msg.sid,
                "from": sender,
                "from_normalized": sender_clean,
                "to": msg.to,
                "body": body,
                "status": msg.status,
                "has_media": has_media,
                "num_media": int(msg.num_media) if msg.num_media else 0,
                "error_code": msg.error_code,
                "error_message": msg.error_message
            },
            priority=priority
        )

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison."""
        import re
        return re.sub(r'[^\d+]', '', phone)

    async def send_sms(self, to: str, body: str, media_url: Optional[str] = None) -> bool:
        """Send an SMS message (requires HITL approval)."""
        if not self.client:
            return False

        try:
            await self.rate_limiter.acquire()

            params = {
                'body': body,
                'from_': self.phone_number,
                'to': to
            }

            if media_url:
                params['media_url'] = [media_url]

            message = self.client.messages.create(**params)
            self.logger.info(f"SMS sent: {message.sid}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send SMS: {e}")
            return False

    async def get_message_history(self, phone_number: str, limit: int = 10) -> List[Dict]:
        """Get message history with a specific number."""
        if not self.client:
            return []

        try:
            await self.rate_limiter.acquire()

            # Get sent messages
            sent = self.client.messages.list(
                from_=self.phone_number,
                to=phone_number,
                limit=limit
            )

            # Get received messages
            received = self.client.messages.list(
                to=self.phone_number,
                from_=phone_number,
                limit=limit
            )

            # Combine and sort
            all_messages = []
            for msg in sent + received:
                all_messages.append({
                    'sid': msg.sid,
                    'direction': msg.direction,
                    'body': msg.body,
                    'date': msg.date_sent.isoformat() if msg.date_sent else None,
                    'status': msg.status
                })

            all_messages.sort(key=lambda x: x['date'] or '', reverse=True)
            return all_messages[:limit]

        except Exception as e:
            self.logger.error(f"Failed to get message history: {e}")
            return []

    async def teardown(self):
        """Clean up SMS watcher resources."""
        self.client = None
