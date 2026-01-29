"""
Calendar Watcher Module
=======================
Monitors Google Calendar for events, reminders, and scheduling conflicts.
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import os

from .base_watcher import BaseWatcher, Event, EventType, generate_event_id, RateLimiter


class CalendarWatcher(BaseWatcher):
    """
    Google Calendar watcher for event monitoring and scheduling.

    Features:
    - New event detection
    - Event modifications tracking
    - Upcoming event reminders
    - Conflict detection
    - Availability checking
    """

    def __init__(
        self,
        check_interval: int = 60,
        config: Optional[Dict] = None,
        credentials_path: str = "config/credentials/calendar_credentials.json",
        reminder_minutes: List[int] = None
    ):
        super().__init__("Calendar", check_interval, config)
        self.credentials_path = credentials_path
        self.token_path = "config/credentials/calendar_token.json"
        self.service = None
        self.reminder_minutes = reminder_minutes or [60, 15]  # 1 hour and 15 min before

        # Track known events
        self.known_events: Dict[str, Dict] = {}
        self.reminded_events: set = set()

        # Rate limiting
        self.rate_limiter = RateLimiter(max_calls=100, period_seconds=60)

    async def setup(self) -> bool:
        """Initialize Google Calendar API connection."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            SCOPES = [
                'https://www.googleapis.com/auth/calendar.readonly',
                'https://www.googleapis.com/auth/calendar.events'
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

                    # Save credentials
                    Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(self.token_path, 'w') as token:
                        token.write(creds.to_json())
                else:
                    self.logger.warning("Calendar credentials not found")
                    return True  # Still return True to allow manual setup later

            self.service = build('calendar', 'v3', credentials=creds)
            self.logger.info("Calendar API connected successfully")

            # Load existing events
            await self._sync_events()
            return True

        except ImportError:
            self.logger.warning(
                "Google Calendar libraries not installed. "
                "Run: pip install google-auth google-auth-oauthlib google-api-python-client"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Calendar: {e}")
            return False

    async def _sync_events(self):
        """Sync events from calendar."""
        if not self.service:
            return

        try:
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=14)).isoformat() + 'Z'

            await self.rate_limiter.acquire()

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=100,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            for event in events:
                self.known_events[event['id']] = {
                    'summary': event.get('summary', 'No Title'),
                    'start': event.get('start', {}).get('dateTime', event.get('start', {}).get('date')),
                    'end': event.get('end', {}).get('dateTime', event.get('end', {}).get('date')),
                    'updated': event.get('updated'),
                    'attendees': event.get('attendees', []),
                    'location': event.get('location'),
                    'description': event.get('description'),
                    'status': event.get('status'),
                    'htmlLink': event.get('htmlLink')
                }

        except Exception as e:
            self.logger.error(f"Failed to sync events: {e}")

    async def check(self) -> List[Event]:
        """Check for calendar updates and reminders."""
        events = []

        if not self.service:
            return events

        try:
            # Check for new/updated events
            new_events = await self._check_event_updates()
            events.extend(new_events)

            # Check for upcoming reminders
            reminders = await self._check_reminders()
            events.extend(reminders)

            # Check for conflicts
            conflicts = await self._check_conflicts()
            events.extend(conflicts)

        except Exception as e:
            self.logger.error(f"Error checking calendar: {e}")

        return events

    async def _check_event_updates(self) -> List[Event]:
        """Check for new or modified events."""
        events = []

        if not self.service:
            return events

        try:
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=14)).isoformat() + 'Z'

            await self.rate_limiter.acquire()

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            calendar_events = events_result.get('items', [])

            for cal_event in calendar_events:
                event_id = cal_event['id']

                if event_id not in self.known_events:
                    # New event
                    event = self._create_event(cal_event, EventType.CALENDAR_EVENT_CREATED)
                    events.append(event)
                    self.known_events[event_id] = cal_event

                elif cal_event.get('updated') != self.known_events[event_id].get('updated'):
                    # Updated event
                    event = self._create_event(cal_event, EventType.CALENDAR_EVENT_UPDATED)
                    events.append(event)
                    self.known_events[event_id] = cal_event

        except Exception as e:
            self.logger.error(f"Error checking event updates: {e}")

        return events

    async def _check_reminders(self) -> List[Event]:
        """Check for events that need reminders."""
        events = []
        now = datetime.now()

        for event_id, event_data in self.known_events.items():
            start_str = event_data.get('start')
            if not start_str:
                continue

            try:
                # Parse start time
                if 'T' in start_str:
                    start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    start_time = start_time.replace(tzinfo=None)
                else:
                    continue  # All-day events don't need minute reminders

                for reminder_mins in self.reminder_minutes:
                    reminder_key = f"{event_id}_{reminder_mins}"

                    if reminder_key in self.reminded_events:
                        continue

                    time_until = (start_time - now).total_seconds() / 60

                    # Trigger reminder if within window
                    if 0 < time_until <= reminder_mins and time_until > (reminder_mins - 5):
                        event = Event(
                            id=generate_event_id("calendar_reminder", event_id),
                            type=EventType.CALENDAR_REMINDER,
                            source="calendar",
                            channel="calendar",
                            timestamp=now,
                            data={
                                "event_id": event_id,
                                "summary": event_data.get('summary'),
                                "start": start_str,
                                "minutes_until": int(time_until),
                                "location": event_data.get('location'),
                                "attendees": [a.get('email') for a in event_data.get('attendees', [])]
                            },
                            priority=2 if reminder_mins <= 15 else 4
                        )
                        events.append(event)
                        self.reminded_events.add(reminder_key)

            except Exception as e:
                self.logger.debug(f"Error checking reminder for {event_id}: {e}")

        return events

    async def _check_conflicts(self) -> List[Event]:
        """Check for scheduling conflicts."""
        events = []
        sorted_events = sorted(
            self.known_events.items(),
            key=lambda x: x[1].get('start', '')
        )

        for i, (id1, event1) in enumerate(sorted_events):
            for id2, event2 in sorted_events[i + 1:]:
                try:
                    start1 = event1.get('start', '')
                    end1 = event1.get('end', '')
                    start2 = event2.get('start', '')

                    if not all([start1, end1, start2]):
                        continue

                    # Simple overlap check
                    if start2 < end1:
                        conflict_key = f"{id1}_{id2}"
                        if conflict_key not in self.reminded_events:
                            event = Event(
                                id=generate_event_id("calendar_conflict", conflict_key),
                                type=EventType.CALENDAR_EVENT_UPDATED,
                                source="calendar",
                                channel="calendar",
                                timestamp=datetime.now(),
                                data={
                                    "conflict_type": "overlap",
                                    "event1": {
                                        "id": id1,
                                        "summary": event1.get('summary'),
                                        "start": start1,
                                        "end": end1
                                    },
                                    "event2": {
                                        "id": id2,
                                        "summary": event2.get('summary'),
                                        "start": start2,
                                        "end": event2.get('end')
                                    }
                                },
                                priority=3
                            )
                            events.append(event)
                            self.reminded_events.add(conflict_key)
                except Exception:
                    pass

        return events

    def _create_event(self, cal_event: Dict, event_type: EventType) -> Event:
        """Create an Event from a calendar event."""
        start = cal_event.get('start', {})
        end = cal_event.get('end', {})

        return Event(
            id=generate_event_id("calendar", cal_event['id']),
            type=event_type,
            source="calendar",
            channel="calendar",
            timestamp=datetime.now(),
            data={
                "event_id": cal_event['id'],
                "summary": cal_event.get('summary', 'No Title'),
                "start": start.get('dateTime', start.get('date')),
                "end": end.get('dateTime', end.get('date')),
                "location": cal_event.get('location'),
                "description": cal_event.get('description'),
                "attendees": [
                    {
                        "email": a.get('email'),
                        "name": a.get('displayName'),
                        "status": a.get('responseStatus')
                    }
                    for a in cal_event.get('attendees', [])
                ],
                "organizer": cal_event.get('organizer', {}).get('email'),
                "html_link": cal_event.get('htmlLink'),
                "status": cal_event.get('status')
            },
            priority=4
        )

    async def get_availability(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int = 30
    ) -> List[Dict]:
        """Get available time slots within a date range."""
        available_slots = []

        if not self.service:
            return available_slots

        try:
            await self.rate_limiter.acquire()

            freebusy = self.service.freebusy().query(body={
                "timeMin": start_date.isoformat() + 'Z',
                "timeMax": end_date.isoformat() + 'Z',
                "items": [{"id": "primary"}]
            }).execute()

            busy_times = freebusy.get('calendars', {}).get('primary', {}).get('busy', [])

            # Find gaps
            current = start_date
            for busy in busy_times:
                busy_start = datetime.fromisoformat(busy['start'].replace('Z', ''))
                busy_end = datetime.fromisoformat(busy['end'].replace('Z', ''))

                if (busy_start - current).total_seconds() >= duration_minutes * 60:
                    available_slots.append({
                        "start": current.isoformat(),
                        "end": busy_start.isoformat()
                    })

                current = busy_end

            # Check remaining time
            if (end_date - current).total_seconds() >= duration_minutes * 60:
                available_slots.append({
                    "start": current.isoformat(),
                    "end": end_date.isoformat()
                })

        except Exception as e:
            self.logger.error(f"Error getting availability: {e}")

        return available_slots

    async def teardown(self):
        """Clean up calendar resources."""
        self.service = None
        self.known_events.clear()
