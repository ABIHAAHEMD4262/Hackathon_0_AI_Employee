#!/usr/bin/env python3
"""
Google API Setup Script for AI Employee
This script helps you authenticate with Gmail and Google Calendar APIs.

BEFORE RUNNING:
1. Download your OAuth credentials from Google Cloud Console
2. Save as: config/credentials/google_credentials.json
3. Run: python scripts/setup_google.py
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check for required packages
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    print("Installing required packages...")
    os.system("pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    print("\nPackages installed! Please run this script again.")
    sys.exit(0)

# Configuration
CREDENTIALS_DIR = Path(__file__).parent.parent / "config" / "credentials"
CREDENTIALS_FILE = CREDENTIALS_DIR / "google_credentials.json"
TOKEN_FILE = CREDENTIALS_DIR / "google_token.json"

# Scopes for Gmail and Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

def setup_credentials():
    """Set up OAuth credentials for Google APIs."""
    print("\n" + "="*60)
    print("  AI EMPLOYEE - Google API Setup")
    print("="*60 + "\n")

    # Check if credentials file exists
    if not CREDENTIALS_FILE.exists():
        print("ERROR: credentials file not found!")
        print(f"\nPlease download your OAuth credentials from Google Cloud Console")
        print(f"and save it as:\n  {CREDENTIALS_FILE}\n")
        print("Steps:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Select your project")
        print("3. Go to APIs & Services > Credentials")
        print("4. Download your OAuth 2.0 Client ID (Desktop app)")
        print("5. Rename the file to 'google_credentials.json'")
        print(f"6. Save it in: {CREDENTIALS_DIR}")
        return None

    creds = None

    # Check if we have a saved token
    if TOKEN_FILE.exists():
        print("Found existing token, loading...")
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # If no valid credentials, do the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            creds.refresh(Request())
        else:
            print("Starting OAuth flow...")
            print("\nA browser window will open. Please sign in with your Google account.\n")

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=8080)

        # Save the token for future use
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"\nToken saved to: {TOKEN_FILE}")

    return creds

def test_gmail(creds):
    """Test Gmail API connection."""
    print("\n" + "-"*40)
    print("Testing Gmail API...")
    print("-"*40)

    try:
        service = build('gmail', 'v1', credentials=creds)

        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        print(f"Connected as: {profile['emailAddress']}")
        print(f"Total messages: {profile['messagesTotal']}")

        # Get recent emails
        results = service.users().messages().list(
            userId='me',
            maxResults=5,
            q='is:unread'
        ).execute()

        messages = results.get('messages', [])
        print(f"\nUnread emails: {len(messages)}")

        if messages:
            print("\nRecent unread emails:")
            for msg in messages[:3]:
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject']
                ).execute()

                headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
                print(f"  - From: {headers.get('From', 'Unknown')[:40]}")
                print(f"    Subject: {headers.get('Subject', 'No Subject')[:50]}")

        print("\n Gmail connection successful!")
        return True

    except Exception as e:
        print(f"\n Gmail error: {e}")
        return False

def test_calendar(creds):
    """Test Google Calendar API connection."""
    print("\n" + "-"*40)
    print("Testing Google Calendar API...")
    print("-"*40)

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Get calendar list
        calendars = service.calendarList().list().execute()
        print(f"Found {len(calendars['items'])} calendars")

        # Get upcoming events
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=5,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        print(f"\nUpcoming events: {len(events)}")

        if events:
            print("\nNext events:")
            for event in events[:3]:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"  - {start[:16]}: {event.get('summary', 'No title')[:40]}")

        print("\n Google Calendar connection successful!")
        return True

    except Exception as e:
        print(f"\n Calendar error: {e}")
        return False

def main():
    """Main setup function."""
    # Ensure credentials directory exists
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

    # Setup credentials
    creds = setup_credentials()
    if not creds:
        return

    print("\n" + "="*60)
    print("  Testing Connections")
    print("="*60)

    # Test Gmail
    gmail_ok = test_gmail(creds)

    # Test Calendar
    calendar_ok = test_calendar(creds)

    # Summary
    print("\n" + "="*60)
    print("  Setup Summary")
    print("="*60)
    print(f"\n  Gmail:    {'Connected' if gmail_ok else 'Failed'}")
    print(f"  Calendar: {'Connected' if calendar_ok else 'Failed'}")

    if gmail_ok and calendar_ok:
        print("\n All services connected successfully!")
        print("\nYour AI Employee can now:")
        print("  - Read and send emails")
        print("  - Access your calendar events")
        print("  - Schedule meetings")
        print("\nToken saved at:")
        print(f"  {TOKEN_FILE}")
    else:
        print("\n Some services failed. Please check the errors above.")

    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
