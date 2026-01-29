"""
WhatsApp Watcher
Monitors WhatsApp Web for important messages using Playwright
"""

import os
import time
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not installed. Run: pip install playwright && playwright install chromium")


class WhatsAppWatcher:
    """
    Watches WhatsApp Web for new messages with priority keywords
    Uses Playwright for browser automation
    """

    def __init__(self, vault_path: str, session_path: str = None):
        """
        Initialize WhatsApp Watcher

        Args:
            vault_path: Path to the AI Employee vault
            session_path: Path to store browser session (for persistent login)
        """
        load_dotenv()

        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action' / 'WhatsApp'
        self.approvals = self.vault_path / 'Approvals'
        self.logs = self.vault_path / 'Logs'

        # Create folders
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.approvals.mkdir(exist_ok=True)
        self.logs.mkdir(exist_ok=True)

        # Session path for persistent login
        self.session_path = Path(session_path) if session_path else self.vault_path / '.whatsapp_session'
        self.session_path.mkdir(exist_ok=True)

        # Track processed messages
        self.processed_file = self.vault_path / '.processed_whatsapp.json'
        self.processed_messages = self._load_processed()

        # Priority keywords that trigger action
        self.priority_keywords = [
            'urgent', 'asap', 'important', 'deadline', 'help',
            'invoice', 'payment', 'contract', 'proposal',
            'meeting', 'call', 'project', 'client', 'order',
            'emergency', 'critical', 'immediately', 'confirm'
        ]

        # Browser instance
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        self.log("WhatsApp Watcher initialized")

    def _load_processed(self) -> Dict:
        """Load processed message IDs"""
        if self.processed_file.exists():
            try:
                return json.loads(self.processed_file.read_text())
            except:
                return {'messages': []}
        return {'messages': []}

    def _save_processed(self, msg_id: str):
        """Save message ID as processed"""
        self.processed_messages['messages'].append(msg_id)
        # Keep only last 1000 messages
        self.processed_messages['messages'] = self.processed_messages['messages'][-1000:]
        self.processed_file.write_text(json.dumps(self.processed_messages, indent=2))

    def log(self, message: str, level: str = 'INFO'):
        """Write to log file"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [WhatsApp] [{level}] {message}"
        print(log_entry)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'daily_{today}.log'
        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')

    def is_priority_message(self, text: str) -> bool:
        """Check if message contains priority keywords"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.priority_keywords)

    def get_priority_level(self, text: str) -> str:
        """Determine priority level based on keywords"""
        text_lower = text.lower()
        high_priority = ['urgent', 'asap', 'emergency', 'critical', 'immediately']
        if any(kw in text_lower for kw in high_priority):
            return 'high'
        return 'medium'

    async def setup_browser(self):
        """Initialize browser with persistent session"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed")

        playwright = await async_playwright().start()

        # Use persistent context for session storage
        self.browser = await playwright.chromium.launch_persistent_context(
            str(self.session_path),
            headless=False,  # Set to True after first login
            args=['--disable-blink-features=AutomationControlled']
        )

        if self.browser.pages:
            self.page = self.browser.pages[0]
        else:
            self.page = await self.browser.new_page()

        self.log("Browser initialized")

    async def login_whatsapp(self):
        """Navigate to WhatsApp Web and wait for login"""
        await self.page.goto('https://web.whatsapp.com')

        self.log("Waiting for WhatsApp Web login...")
        self.log("Please scan QR code with your phone if prompted")

        # Wait for main chat list to appear (indicates successful login)
        try:
            await self.page.wait_for_selector(
                '[data-testid="chat-list"]',
                timeout=120000  # 2 minutes to scan QR
            )
            self.log("Successfully logged into WhatsApp Web")
            return True
        except Exception as e:
            self.log(f"Login timeout or error: {e}", 'ERROR')
            return False

    async def get_unread_chats(self) -> List[Dict]:
        """Get list of chats with unread messages"""
        unread_chats = []

        try:
            # Find all chat items with unread badge
            chat_elements = await self.page.query_selector_all('[data-testid="cell-frame-container"]')

            for chat in chat_elements:
                try:
                    # Check for unread indicator
                    unread_badge = await chat.query_selector('[data-testid="icon-unread-count"]')
                    if not unread_badge:
                        continue

                    # Get chat name
                    name_elem = await chat.query_selector('[data-testid="cell-frame-title"]')
                    chat_name = await name_elem.inner_text() if name_elem else "Unknown"

                    # Get last message preview
                    preview_elem = await chat.query_selector('[data-testid="last-msg-status"]')
                    preview = await preview_elem.inner_text() if preview_elem else ""

                    # Get unread count
                    count_text = await unread_badge.inner_text()
                    unread_count = int(count_text) if count_text.isdigit() else 1

                    unread_chats.append({
                        'name': chat_name,
                        'preview': preview,
                        'unread_count': unread_count,
                        'element': chat
                    })

                except Exception as e:
                    continue

        except Exception as e:
            self.log(f"Error getting unread chats: {e}", 'ERROR')

        return unread_chats

    async def read_chat_messages(self, chat_element) -> List[Dict]:
        """Click on a chat and read the messages"""
        messages = []

        try:
            # Click on the chat
            await chat_element.click()
            await asyncio.sleep(1)  # Wait for chat to load

            # Get message elements
            msg_elements = await self.page.query_selector_all('[data-testid="msg-container"]')

            for msg in msg_elements[-10:]:  # Last 10 messages
                try:
                    # Get message text
                    text_elem = await msg.query_selector('[data-testid="balloon-text"]')
                    if not text_elem:
                        continue

                    text = await text_elem.inner_text()

                    # Check if incoming message (not from us)
                    is_incoming = await msg.query_selector('[data-testid="msg-meta"]')

                    # Get timestamp if available
                    time_elem = await msg.query_selector('[data-testid="msg-time"]')
                    timestamp = await time_elem.inner_text() if time_elem else ""

                    messages.append({
                        'text': text,
                        'timestamp': timestamp,
                        'is_incoming': is_incoming is not None
                    })

                except Exception as e:
                    continue

        except Exception as e:
            self.log(f"Error reading messages: {e}", 'ERROR')

        return messages

    def create_action_file(self, chat_name: str, messages: List[Dict]) -> Path:
        """Create action file for WhatsApp messages"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = "".join(c if c.isalnum() or c in ' -_' else '_' for c in chat_name[:20])

        filename = f"WHATSAPP_{timestamp}_{safe_name}.md"
        filepath = self.needs_action / filename

        # Combine messages
        msg_text = "\n".join([
            f"[{m['timestamp']}] {m['text']}"
            for m in messages if m.get('is_incoming')
        ])

        priority = self.get_priority_level(msg_text)

        content = f"""---
type: whatsapp
from: {chat_name}
received: {datetime.now().isoformat()}
priority: {priority}
status: pending
message_count: {len(messages)}
---

## WhatsApp Messages from {chat_name}

**Priority:** {priority.upper()}

**Received:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Messages

{msg_text}

---

## Suggested Actions

- [ ] Read and understand the messages
- [ ] Draft appropriate response
- [ ] Move to Approvals if response needed
- [ ] Mark as Done when complete
"""

        filepath.write_text(content, encoding='utf-8')
        self.log(f"Created action file: {filename}")

        return filepath

    def create_reply_draft(self, chat_name: str, messages: List[Dict]) -> Optional[Path]:
        """Create a draft reply for approval"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"whatsapp-reply-{timestamp}.md"
        filepath = self.approvals / filename

        # Get last incoming message
        incoming = [m for m in messages if m.get('is_incoming')]
        last_msg = incoming[-1]['text'] if incoming else "No message"

        content = f"""---
type: whatsapp_reply
title: Reply to {chat_name}
status: pending
created: {datetime.now().isoformat()}
to: {chat_name}
---

# WhatsApp Reply Draft

**To:** {chat_name}

---

Hi,

Thank you for your message. I have received it and will respond shortly.

Best regards

---

*This draft was generated by AI Employee. Please review and approve before sending.*

## Original Message

> {last_msg[:500]}
"""

        filepath.write_text(content, encoding='utf-8')
        self.log(f"Created reply draft: {filename}")

        return filepath

    async def check_for_messages(self) -> int:
        """Check for new priority messages"""
        processed_count = 0

        try:
            unread_chats = await self.get_unread_chats()
            self.log(f"Found {len(unread_chats)} chats with unread messages")

            for chat in unread_chats:
                chat_name = chat['name']
                msg_id = f"{chat_name}_{datetime.now().strftime('%Y%m%d_%H')}"

                # Skip if already processed recently
                if msg_id in self.processed_messages['messages']:
                    continue

                # Read messages from this chat
                messages = await self.read_chat_messages(chat['element'])

                # Check for priority keywords
                all_text = " ".join([m['text'] for m in messages])

                if self.is_priority_message(all_text):
                    self.log(f"Priority message detected from {chat_name}")

                    # Create action file
                    self.create_action_file(chat_name, messages)

                    # Create reply draft for high priority
                    if self.get_priority_level(all_text) == 'high':
                        self.create_reply_draft(chat_name, messages)

                    processed_count += 1

                self._save_processed(msg_id)

                # Go back to chat list
                await asyncio.sleep(0.5)

        except Exception as e:
            self.log(f"Error checking messages: {e}", 'ERROR')

        return processed_count

    async def run_once(self):
        """Run a single check"""
        self.log("Running single WhatsApp check...")

        await self.setup_browser()
        logged_in = await self.login_whatsapp()

        if logged_in:
            count = await self.check_for_messages()
            self.log(f"Processed {count} priority messages")

        if self.browser:
            await self.browser.close()

    async def run(self, interval: int = 60):
        """Run continuously"""
        self.log(f"Starting WhatsApp Watcher (checking every {interval}s)")

        await self.setup_browser()
        logged_in = await self.login_whatsapp()

        if not logged_in:
            self.log("Failed to login to WhatsApp", 'ERROR')
            return

        while True:
            try:
                count = await self.check_for_messages()
                if count > 0:
                    self.log(f"Processed {count} new priority messages")
            except Exception as e:
                self.log(f"Error in main loop: {e}", 'ERROR')

            await asyncio.sleep(interval)


def main():
    """Main entry point"""
    import sys

    load_dotenv()

    vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent))

    print("=" * 50)
    print("  WhatsApp Watcher")
    print("=" * 50)
    print(f"Vault: {vault_path}")
    print()

    if not PLAYWRIGHT_AVAILABLE:
        print("ERROR: Playwright not installed!")
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    watcher = WhatsAppWatcher(vault_path)

    if '--test' in sys.argv or '-t' in sys.argv:
        print("Running in TEST mode - single check only")
        print("A browser window will open. Scan QR code to login.\n")
        asyncio.run(watcher.run_once())
    else:
        print("Running continuously. Press Ctrl+C to stop.")
        print("A browser window will open. Scan QR code to login.\n")
        try:
            asyncio.run(watcher.run())
        except KeyboardInterrupt:
            print("\n\nShutdown requested. Goodbye!")


if __name__ == '__main__':
    main()
