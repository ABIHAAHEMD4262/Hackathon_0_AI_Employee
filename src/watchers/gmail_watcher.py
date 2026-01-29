"""
Gmail Watcher Module
====================
Monitors Gmail for new emails, categorizes them, and triggers processing.
"""

import asyncio
import base64
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import email
from email.header import decode_header
import re

from .base_watcher import BaseWatcher, Event, EventType, generate_event_id, RateLimiter


class GmailWatcher(BaseWatcher):
    """
    Gmail watcher using Google Gmail API.

    Features:
    - New email detection
    - VIP sender prioritization
    - Automatic categorization
    - Attachment detection
    - Thread tracking
    """

    def __init__(
        self,
        check_interval: int = 60,
        config: Optional[Dict] = None,
        credentials_path: str = "config/credentials/gmail_credentials.json"
    ):
        super().__init__("Gmail", check_interval, config)
        self.credentials_path = credentials_path
        self.token_path = "config/credentials/gmail_token.json"
        self.service = None

        # Track seen messages
        self.seen_message_ids: set = set()
        self.last_history_id: Optional[str] = None

        # VIP senders for priority handling
        self.vip_senders: List[str] = config.get("vip_senders", []) if config else []
        self.blacklist: List[str] = config.get("blacklist", []) if config else []

        # Categorization keywords
        self.urgent_keywords = ['urgent', 'asap', 'emergency', 'immediate', 'critical']
        self.financial_keywords = ['invoice', 'payment', 'bill', 'receipt', 'transaction', 'wire']
        self.meeting_keywords = ['meeting', 'schedule', 'calendar', 'call', 'appointment', 'zoom', 'teams']

        # Rate limiting
        self.rate_limiter = RateLimiter(max_calls=50, period_seconds=60)

    async def setup(self) -> bool:
        """Initialize Gmail API connection."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            SCOPES = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/gmail.send'
            ]

            creds = None

            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif os.path.exists(self.credentials_path):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                    from pathlib import Path
                    Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                else:
                    self.logger.warning("Gmail credentials not found")
                    return True

            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail API connected successfully")
            return True

        except ImportError:
            self.logger.warning(
                "Google Gmail libraries not installed. "
                "Run: pip install google-auth google-auth-oauthlib google-api-python-client"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Gmail: {e}")
            return False

    async def check(self) -> List[Event]:
        """Check for new Gmail messages."""
        events = []

        if not self.service:
            return events

        try:
            await self.rate_limiter.acquire()

            # Get recent unread messages
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=20
            ).execute()

            messages = results.get('messages', [])

            for msg_ref in messages:
                msg_id = msg_ref['id']

                if msg_id in self.seen_message_ids:
                    continue

                self.seen_message_ids.add(msg_id)

                # Get full message
                await self.rate_limiter.acquire()
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()

                event = self._create_email_event(message)
                if event:
                    events.append(event)

            # Cleanup old seen IDs (keep last 1000)
            if len(self.seen_message_ids) > 1000:
                self.seen_message_ids = set(list(self.seen_message_ids)[-500:])

        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")

        return events

    def _create_email_event(self, message: Dict) -> Optional[Event]:
        """Create an Event from a Gmail message."""
        try:
            headers = {
                h['name'].lower(): h['value']
                for h in message['payload']['headers']
            }

            sender = headers.get('from', '')
            subject = headers.get('subject', '(No Subject)')
            date_str = headers.get('date', '')
            to = headers.get('to', '')
            cc = headers.get('cc', '')
            reply_to = headers.get('reply-to', '')

            # Extract sender email
            sender_email = self._extract_email(sender)
            sender_name = self._extract_name(sender)

            # Check blacklist
            if any(bl.lower() in sender_email.lower() for bl in self.blacklist):
                return None

            # Get snippet/preview
            snippet = message.get('snippet', '')

            # Check for attachments
            attachments = self._get_attachments(message['payload'])

            # Get body
            body = self._get_body(message['payload'])

            # Categorize
            category = self._categorize_email(subject, body, sender_email)

            # Determine priority
            priority = self._calculate_priority(sender_email, subject, body, category)

            return Event(
                id=generate_event_id("email", message['id']),
                type=EventType.EMAIL_RECEIVED,
                source="gmail",
                channel="email",
                timestamp=datetime.now(),
                data={
                    "message_id": message['id'],
                    "thread_id": message['threadId'],
                    "from": sender,
                    "from_email": sender_email,
                    "from_name": sender_name,
                    "to": to,
                    "cc": cc,
                    "reply_to": reply_to,
                    "subject": subject,
                    "snippet": snippet,
                    "body_preview": body[:500] if body else snippet,
                    "date": date_str,
                    "labels": message.get('labelIds', []),
                    "category": category,
                    "attachments": attachments,
                    "has_attachments": len(attachments) > 0,
                    "is_reply": subject.lower().startswith('re:'),
                    "is_forward": subject.lower().startswith('fwd:')
                },
                priority=priority
            )

        except Exception as e:
            self.logger.error(f"Error creating email event: {e}")
            return None

    def _extract_email(self, sender: str) -> str:
        """Extract email address from sender string."""
        match = re.search(r'<(.+?)>', sender)
        if match:
            return match.group(1)
        return sender.strip()

    def _extract_name(self, sender: str) -> str:
        """Extract name from sender string."""
        match = re.search(r'^(.+?)\s*<', sender)
        if match:
            name = match.group(1).strip('" ')
            return name
        return sender.split('@')[0]

    def _get_attachments(self, payload: Dict) -> List[Dict]:
        """Extract attachment information."""
        attachments = []

        parts = payload.get('parts', [])
        for part in parts:
            if part.get('filename'):
                attachments.append({
                    'filename': part['filename'],
                    'mime_type': part.get('mimeType'),
                    'size': part.get('body', {}).get('size', 0)
                })

            # Check nested parts
            if 'parts' in part:
                attachments.extend(self._get_attachments(part))

        return attachments

    def _get_body(self, payload: Dict) -> str:
        """Extract email body text."""
        body = ""

        if 'body' in payload and payload['body'].get('data'):
            try:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            except Exception:
                pass

        parts = payload.get('parts', [])
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                if part.get('body', {}).get('data'):
                    try:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                    except Exception:
                        pass

        return body

    def _categorize_email(self, subject: str, body: str, sender: str) -> str:
        """Categorize email based on content."""
        text = f"{subject} {body}".lower()

        if any(kw in text for kw in self.financial_keywords):
            return 'financial'
        elif any(kw in text for kw in self.meeting_keywords):
            return 'meeting'
        elif any(kw in text for kw in self.urgent_keywords):
            return 'urgent'
        elif 'unsubscribe' in text.lower():
            return 'marketing'
        else:
            return 'general'

    def _calculate_priority(
        self,
        sender_email: str,
        subject: str,
        body: str,
        category: str
    ) -> int:
        """Calculate email priority (1=highest, 10=lowest)."""
        priority = 5
        text = f"{subject} {body}".lower()

        # VIP sender
        if any(vip.lower() in sender_email.lower() for vip in self.vip_senders):
            priority = 1

        # Category-based priority
        elif category == 'urgent':
            priority = 2
        elif category == 'financial':
            priority = 3
        elif category == 'meeting':
            priority = 4
        elif category == 'marketing':
            priority = 8

        # Keyword adjustments
        if any(kw in text for kw in self.urgent_keywords):
            priority = min(priority, 2)

        return priority

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_id: Optional[str] = None
    ) -> bool:
        """Send an email (requires HITL approval)."""
        if not self.service:
            return False

        try:
            import base64
            from email.mime.text import MIMEText

            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            body = {'raw': raw}
            if reply_to_id:
                body['threadId'] = reply_to_id

            await self.rate_limiter.acquire()
            self.service.users().messages().send(
                userId='me',
                body=body
            ).execute()

            return True

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read."""
        if not self.service:
            return False

        try:
            await self.rate_limiter.acquire()
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark as read: {e}")
            return False

    async def teardown(self):
        """Clean up Gmail resources."""
        self.service = None
        self.seen_message_ids.clear()
