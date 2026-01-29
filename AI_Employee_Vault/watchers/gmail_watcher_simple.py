"""
Simple Gmail Watcher using IMAP
Works with Gmail App Password - no OAuth setup required
"""

import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import time
from dotenv import load_dotenv


class SimpleGmailWatcher:
    """
    Simple Gmail watcher using IMAP
    Uses app password for authentication
    """

    def __init__(self, vault_path: str):
        """
        Initialize Gmail Watcher

        Args:
            vault_path: Path to the AI Employee vault
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.approvals = self.vault_path / 'Approvals'
        self.logs = self.vault_path / 'Logs'

        # Create folders
        self.needs_action.mkdir(exist_ok=True)
        self.approvals.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)
        (self.needs_action / 'Emails').mkdir(exist_ok=True)

        # Track processed emails
        self.processed_file = self.vault_path / '.processed_emails.txt'
        self.processed_ids = self._load_processed()

        # Gmail credentials
        self.email_user = os.getenv('EMAIL_USER') or os.getenv('GMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS') or os.getenv('GMAIL_APP_PASSWORD')

        if not self.email_user or not self.email_pass:
            raise ValueError(
                "Missing Gmail credentials. Set EMAIL_USER and EMAIL_PASS in .env file"
            )

        # Clean password (remove spaces if any)
        self.email_pass = self.email_pass.replace(' ', '')

        # Priority keywords
        self.priority_keywords = [
            'urgent', 'asap', 'important', 'deadline',
            'invoice', 'payment', 'contract', 'proposal',
            'meeting', 'call', 'project', 'client'
        ]

        self.log(f"Gmail Watcher initialized for {self.email_user}")

    def _load_processed(self) -> set:
        """Load set of processed email IDs"""
        if self.processed_file.exists():
            return set(self.processed_file.read_text().strip().split('\n'))
        return set()

    def _save_processed(self, email_id: str):
        """Save email ID as processed"""
        self.processed_ids.add(email_id)
        with open(self.processed_file, 'a') as f:
            f.write(f"{email_id}\n")

    def log(self, message: str, level: str = 'INFO'):
        """Write to log file"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'daily_{today}.log'
        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')

    def connect(self) -> imaplib.IMAP4_SSL:
        """Connect to Gmail IMAP"""
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.email_user, self.email_pass)
            self.log("Connected to Gmail IMAP")
            return mail
        except Exception as e:
            self.log(f"Failed to connect to Gmail: {e}", 'ERROR')
            raise

    def decode_email_header(self, header: str) -> str:
        """Decode email header (handles encoded subjects)"""
        if header is None:
            return ""
        decoded_parts = decode_header(header)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                result.append(part)
        return ''.join(result)

    def get_email_body(self, msg) -> str:
        """Extract email body from message"""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            except:
                body = str(msg.get_payload())

        return body[:2000]  # Limit body length

    def assess_priority(self, subject: str, body: str) -> str:
        """Determine email priority"""
        text = (subject + ' ' + body).lower()
        for keyword in self.priority_keywords:
            if keyword in text:
                return 'high'
        return 'medium'

    def check_for_emails(self) -> List[Dict]:
        """Check for new unread emails"""
        new_emails = []

        try:
            mail = self.connect()
            mail.select('INBOX')

            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')

            if status != 'OK':
                self.log("No messages found", 'WARNING')
                return []

            email_ids = messages[0].split()
            self.log(f"Found {len(email_ids)} unread emails")

            for email_id in email_ids[-10:]:  # Process last 10
                email_id_str = email_id.decode()

                if email_id_str in self.processed_ids:
                    continue

                # Fetch email
                status, msg_data = mail.fetch(email_id, '(RFC822)')

                if status != 'OK':
                    continue

                # Parse email
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Extract details
                subject = self.decode_email_header(msg['Subject'])
                from_addr = self.decode_email_header(msg['From'])
                date = msg['Date']
                body = self.get_email_body(msg)

                new_emails.append({
                    'id': email_id_str,
                    'subject': subject,
                    'from': from_addr,
                    'date': date,
                    'body': body,
                    'priority': self.assess_priority(subject, body)
                })

                self._save_processed(email_id_str)
                self.log(f"New email: {subject[:50]}...")

            mail.logout()

        except Exception as e:
            self.log(f"Error checking emails: {e}", 'ERROR')

        return new_emails

    def create_action_file(self, email_data: Dict) -> Path:
        """Create action file for new email"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_subject = "".join(c if c.isalnum() or c in ' -_' else '_'
                               for c in email_data['subject'][:30])

        filename = f"EMAIL_{timestamp}_{safe_subject}.md"
        filepath = self.needs_action / 'Emails' / filename

        content = f"""---
type: email
from: {email_data['from']}
subject: {email_data['subject']}
received: {datetime.now().isoformat()}
priority: {email_data['priority']}
status: pending
email_id: {email_data['id']}
---

## Email from {email_data['from'].split('<')[0].strip()}

**Subject:** {email_data['subject']}

**Date:** {email_data['date']}

**Priority:** {email_data['priority'].upper()}

---

## Email Content

{email_data['body']}

---

## Suggested Actions

- [ ] Read and understand the email
- [ ] Draft appropriate response
- [ ] Move to Approvals if response needed
- [ ] Mark as Done when complete
"""

        filepath.write_text(content, encoding='utf-8')
        self.log(f"Created action file: {filename}")

        return filepath

    def create_draft_response(self, email_data: Dict) -> Optional[Path]:
        """Create a draft response for approval"""
        if email_data['priority'] != 'high':
            return None

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"email-reply-{timestamp}.md"
        filepath = self.approvals / filename

        # Extract sender email
        from_addr = email_data['from']
        if '<' in from_addr:
            reply_to = from_addr.split('<')[1].split('>')[0]
            sender_name = from_addr.split('<')[0].strip()
        else:
            reply_to = from_addr
            sender_name = from_addr.split('@')[0]

        content = f"""---
type: email_draft
title: Re: {email_data['subject']}
status: pending
created: {datetime.now().isoformat()}
to: {reply_to}
subject: Re: {email_data['subject']}
original_id: {email_data['id']}
---

# Email Draft

**To:** {reply_to}
**Subject:** Re: {email_data['subject']}

---

Dear {sender_name},

Thank you for your email regarding "{email_data['subject']}".

I have received your message and will review it carefully. I will get back to you with a detailed response shortly.

Best regards,
Abiha

---

*This draft was generated by AI Employee. Please review and approve before sending.*

## Original Email

> From: {email_data['from']}
> Subject: {email_data['subject']}
>
> {email_data['body'][:500]}...
"""

        filepath.write_text(content, encoding='utf-8')
        self.log(f"Created draft response for approval: {filename}")

        return filepath

    def run_once(self):
        """Run a single check"""
        self.log("Running single email check...")

        emails = self.check_for_emails()

        if not emails:
            self.log("No new emails found")
            return

        for email_data in emails:
            # Create action file
            self.create_action_file(email_data)

            # Create draft response for high priority
            if email_data['priority'] == 'high':
                self.create_draft_response(email_data)

        self.log(f"Processed {len(emails)} new emails")

    def run(self, interval: int = 120):
        """Run continuously"""
        self.log(f"Starting Gmail Watcher (checking every {interval}s)")

        while True:
            try:
                self.run_once()
            except Exception as e:
                self.log(f"Error in main loop: {e}", 'ERROR')

            time.sleep(interval)


def main():
    """Main entry point"""
    import sys

    # Load environment variables
    load_dotenv()

    # Get vault path
    vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent))

    print("=" * 50)
    print("  Simple Gmail Watcher")
    print("=" * 50)
    print(f"Vault: {vault_path}")
    print()

    try:
        watcher = SimpleGmailWatcher(vault_path)

        if '--test' in sys.argv or '-t' in sys.argv:
            print("Running in TEST mode - single check only\n")
            watcher.run_once()
        else:
            print("Running continuously. Press Ctrl+C to stop.\n")
            watcher.run()

    except ValueError as e:
        print(f"\nERROR: {e}")
        print("\nSetup instructions:")
        print("1. Create a .env file in the vault root")
        print("2. Add: EMAIL_USER=your-email@gmail.com")
        print("3. Add: EMAIL_PASS=your-app-password")
        print("\nTo get an app password:")
        print("  Google Account > Security > 2-Step Verification > App Passwords")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nShutdown requested. Goodbye!")
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
