"""
Gmail Watcher
Monitors Gmail inbox for important emails and creates action files
"""

import os
import base64
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from base_watcher import BaseWatcher


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail inbox for new important emails
    """

    def __init__(
        self,
        vault_path: str,
        credentials_path: str,
        token_path: str = 'token.json',
        check_interval: int = 120  # 2 minutes
    ):
        """
        Initialize Gmail Watcher

        Args:
            vault_path: Path to Obsidian vault
            credentials_path: Path to Gmail API credentials.json
            token_path: Path to store OAuth token
            check_interval: Seconds between checks
        """
        super().__init__(vault_path, check_interval)

        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.service = None

        # Keywords that make an email high priority
        self.priority_keywords = [
            'urgent', 'asap', 'important', 'deadline',
            'invoice', 'payment', 'contract', 'proposal',
            'meeting', 'call', 'project', 'client'
        ]

        # Initialize Gmail API
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API"""
        creds = None

        # Load existing token if available
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path), SCOPES
                )
                self.logger.info('Loaded existing Gmail credentials')
            except Exception as e:
                self.logger.error(f'Error loading credentials: {e}')

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.info('Refreshed Gmail credentials')
                except Exception as e:
                    self.logger.error(f'Error refreshing credentials: {e}')
                    creds = None

            if not creds:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f'Gmail credentials not found at {self.credentials_path}. '
                        'Please download from Google Cloud Console.'
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
                self.logger.info('Completed Gmail authentication')

            # Save credentials
            self.token_path.write_text(creds.to_json())
            self.logger.info(f'Saved credentials to {self.token_path}')

        # Build Gmail service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info('Gmail API service initialized')
        except Exception as e:
            self.logger.error(f'Error building Gmail service: {e}')
            raise

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check Gmail for new unread important emails

        Returns:
            List of new email message dicts
        """
        try:
            # Query for unread emails (can refine this query)
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',  # Only unread emails
                maxResults=10  # Limit to recent 10
            ).execute()

            messages = results.get('messages', [])

            # Filter out already processed
            new_messages = []
            for msg in messages:
                if not self.is_processed(msg['id']):
                    # Get full message details
                    full_msg = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    new_messages.append(full_msg)
                    self.mark_processed(msg['id'])

            return new_messages

        except HttpError as e:
            self.logger.error(f'Gmail API error: {e}')
            return []
        except Exception as e:
            self.logger.error(f'Error checking Gmail: {e}')
            return []

    def _extract_headers(self, message: Dict) -> Dict[str, str]:
        """Extract useful headers from Gmail message"""
        headers = {}
        for header in message['payload'].get('headers', []):
            name = header['name']
            if name in ['From', 'To', 'Subject', 'Date']:
                headers[name] = header['value']
        return headers

    def _extract_body(self, message: Dict) -> str:
        """Extract email body from Gmail message"""
        try:
            # Try to get plain text body
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')

            # Fallback to snippet
            return message.get('snippet', '')
        except Exception as e:
            self.logger.error(f'Error extracting body: {e}')
            return message.get('snippet', 'Could not extract email body')

    def _assess_priority(self, headers: Dict, body: str) -> str:
        """
        Determine email priority based on keywords

        Returns:
            'high', 'medium', or 'low'
        """
        subject = headers.get('Subject', '').lower()
        body_lower = body.lower()

        # Check for priority keywords
        for keyword in self.priority_keywords:
            if keyword in subject or keyword in body_lower:
                return 'high'

        return 'medium'

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create action file for new email

        Args:
            item: Gmail message dict

        Returns:
            Path to created file
        """
        # Extract email details
        headers = self._extract_headers(item)
        body = self._extract_body(item)
        priority = self._assess_priority(headers, body)

        # Get sender email
        from_header = headers.get('From', 'Unknown')
        # Extract just email address if possible
        if '<' in from_header:
            sender = from_header.split('<')[1].split('>')[0]
        else:
            sender = from_header.split('@')[0] if '@' in from_header else from_header

        # Create frontmatter
        frontmatter_data = {
            'type': 'email',
            'from': headers.get('From', 'Unknown'),
            'subject': headers.get('Subject', 'No Subject'),
            'received': datetime.now().isoformat(),
            'priority': priority,
            'status': 'pending',
            'gmail_id': item['id']
        }

        # Build markdown content
        content = self.generate_frontmatter(frontmatter_data)
        content += f"## Email from {sender}\n\n"
        content += f"**Subject:** {headers.get('Subject', 'No Subject')}\n\n"
        content += f"**Date:** {headers.get('Date', 'Unknown')}\n\n"
        content += f"**Priority:** {priority.upper()}\n\n"
        content += "---\n\n"
        content += "## Email Content\n\n"
        content += body + "\n\n"
        content += "---\n\n"
        content += "## Suggested Actions\n\n"
        content += "- [ ] Read and understand the email\n"
        content += "- [ ] Draft appropriate response\n"
        content += "- [ ] Move to Pending_Approval if response needed\n"
        content += "- [ ] Mark as Done when complete\n\n"

        # Create safe filename
        safe_subject = self.sanitize_filename(
            headers.get('Subject', 'no_subject')
        )
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'EMAIL_{timestamp}_{safe_subject}.md'

        # Write to Needs_Action/Emails
        email_folder = self.needs_action / 'Emails'
        email_folder.mkdir(exist_ok=True)
        filepath = email_folder / filename

        filepath.write_text(content, encoding='utf-8')

        return filepath


def main():
    """
    Main entry point for Gmail Watcher
    """
    import sys
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Get paths from environment or use defaults
    vault_path = os.getenv('VAULT_PATH', '../')
    credentials_path = os.getenv('GMAIL_CREDENTIALS', 'credentials.json')

    # Check if running in test mode
    test_mode = '--test' in sys.argv

    try:
        # Create watcher
        watcher = GmailWatcher(
            vault_path=vault_path,
            credentials_path=credentials_path
        )

        if test_mode:
            print("Running in TEST mode - single check only")
            watcher.run_once()
        else:
            print("Starting Gmail Watcher...")
            print("Press Ctrl+C to stop")
            watcher.run()

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("\nTo set up Gmail API:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Create a project (or select existing)")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download credentials.json")
        print("6. Place in watchers/ directory")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
