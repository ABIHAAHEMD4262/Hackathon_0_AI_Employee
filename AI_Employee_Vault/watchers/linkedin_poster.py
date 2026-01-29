"""
LinkedIn Auto-Poster
Posts approved content to LinkedIn using browser automation
"""

import os
import time
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv

try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class LinkedInPoster:
    """
    Posts content to LinkedIn using browser automation
    Requires human approval before posting
    """

    def __init__(self, vault_path: str, session_path: str = None):
        load_dotenv()

        self.vault_path = Path(vault_path)
        self.approvals = self.vault_path / 'Approvals'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'

        # Session for persistent login
        self.session_path = Path(session_path) if session_path else self.vault_path / '.linkedin_session'
        self.session_path.mkdir(exist_ok=True)

        # Browser
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        self.log("LinkedIn Poster initialized")

    def log(self, message: str, level: str = 'INFO'):
        """Log message"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [LinkedIn] [{level}] {message}"
        print(log_entry)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'daily_{today}.log'
        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')

    async def setup_browser(self):
        """Initialize browser"""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed")

        playwright = await async_playwright().start()

        self.browser = await playwright.chromium.launch_persistent_context(
            str(self.session_path),
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )

        if self.browser.pages:
            self.page = self.browser.pages[0]
        else:
            self.page = await self.browser.new_page()

        self.log("Browser initialized")

    async def login(self) -> bool:
        """Login to LinkedIn"""
        await self.page.goto('https://www.linkedin.com/feed/')

        # Check if already logged in
        try:
            await self.page.wait_for_selector('[data-control-name="identity_welcome_message"]', timeout=5000)
            self.log("Already logged into LinkedIn")
            return True
        except:
            pass

        # Check if on login page
        if 'login' in self.page.url or 'signin' in self.page.url:
            self.log("Please login to LinkedIn in the browser window")
            self.log("Waiting for login...")

            # Wait for feed page (indicates successful login)
            try:
                await self.page.wait_for_url('**/feed/**', timeout=120000)
                self.log("Successfully logged into LinkedIn")
                return True
            except:
                self.log("Login timeout", 'ERROR')
                return False

        return True

    async def create_post(self, content: str) -> bool:
        """Create a new LinkedIn post"""
        try:
            # Navigate to feed
            await self.page.goto('https://www.linkedin.com/feed/')
            await asyncio.sleep(2)

            # Click "Start a post" button
            start_post_btn = await self.page.wait_for_selector(
                'button[class*="share-box-feed-entry__trigger"]',
                timeout=10000
            )
            await start_post_btn.click()
            await asyncio.sleep(1)

            # Wait for post modal
            text_area = await self.page.wait_for_selector(
                '[data-test-ql-editor-contenteditable="true"]',
                timeout=10000
            )

            # Type the content
            await text_area.fill(content)
            await asyncio.sleep(1)

            # Click Post button
            post_btn = await self.page.wait_for_selector(
                'button[class*="share-actions__primary-action"]',
                timeout=5000
            )
            await post_btn.click()

            await asyncio.sleep(3)

            self.log("Post created successfully!")
            return True

        except Exception as e:
            self.log(f"Error creating post: {e}", 'ERROR')
            return False

    def parse_linkedin_post(self, file_path: Path) -> Optional[Dict]:
        """Parse LinkedIn post file"""
        try:
            content = file_path.read_text(encoding='utf-8')

            # Extract content between --- markers (after frontmatter)
            parts = content.split('---')
            if len(parts) >= 3:
                body = parts[2].strip()

                # Remove markdown formatting for LinkedIn
                body = body.replace('# ', '').replace('## ', '').replace('**', '')
                body = body.replace('*This', '\n\n*This')  # Keep AI notice

                return {
                    'content': body,
                    'file_path': file_path
                }

        except Exception as e:
            self.log(f"Error parsing file: {e}", 'ERROR')

        return None

    async def process_approved_posts(self):
        """Process all approved LinkedIn posts"""
        # Look for approved LinkedIn posts
        approved_files = list(self.approved.glob('*linkedin*.md'))

        if not approved_files:
            self.log("No approved LinkedIn posts found")
            return 0

        posted_count = 0

        for file_path in approved_files:
            post_data = self.parse_linkedin_post(file_path)

            if not post_data:
                continue

            self.log(f"Posting: {file_path.name}")

            success = await self.create_post(post_data['content'])

            if success:
                # Move to Done
                new_path = self.done / file_path.name
                file_path.rename(new_path)
                self.log(f"Moved to Done: {file_path.name}")
                posted_count += 1
            else:
                self.log(f"Failed to post: {file_path.name}", 'ERROR')

        return posted_count

    def create_post_draft(self, topic: str, style: str = 'professional') -> Path:
        """Create a draft LinkedIn post for approval"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"linkedin-post-{timestamp}.md"
        filepath = self.approvals / filename

        # Generate post content based on topic
        if style == 'professional':
            content = f"""---
type: linkedin_post
title: LinkedIn Post about {topic}
status: pending
created: {datetime.now().isoformat()}
platform: linkedin
---

# LinkedIn Post Draft

---

{topic}

I'm excited to share my thoughts on this topic.

Key takeaways:
• Point 1
• Point 2
• Point 3

What are your thoughts? Let me know in the comments!

#Technology #Innovation #CareerGrowth

---

*This post was drafted by AI Employee. Please review and edit before approving.*
"""
        else:
            content = f"""---
type: linkedin_post
title: LinkedIn Post about {topic}
status: pending
created: {datetime.now().isoformat()}
platform: linkedin
---

# LinkedIn Post Draft

---

{topic}

---

*This post was drafted by AI Employee. Please review and edit before approving.*
"""

        filepath.write_text(content, encoding='utf-8')
        self.log(f"Created draft: {filename}")

        return filepath

    async def run_once(self):
        """Process approved posts once"""
        await self.setup_browser()

        if not await self.login():
            self.log("Failed to login", 'ERROR')
            return

        count = await self.process_approved_posts()
        self.log(f"Posted {count} items")

        await self.browser.close()

    async def run(self, interval: int = 300):
        """Run continuously"""
        await self.setup_browser()

        if not await self.login():
            self.log("Failed to login", 'ERROR')
            return

        self.log(f"Running continuously (checking every {interval}s)")

        while True:
            try:
                await self.process_approved_posts()
            except Exception as e:
                self.log(f"Error: {e}", 'ERROR')

            await asyncio.sleep(interval)


def main():
    """Main entry point"""
    import sys

    load_dotenv()

    vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent))

    print("=" * 50)
    print("  LinkedIn Auto-Poster")
    print("=" * 50)
    print(f"Vault: {vault_path}")
    print()

    if not PLAYWRIGHT_AVAILABLE:
        print("ERROR: Playwright not installed!")
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    poster = LinkedInPoster(vault_path)

    if '--draft' in sys.argv:
        # Create a draft post
        idx = sys.argv.index('--draft')
        topic = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "My latest update"
        poster.create_post_draft(topic)
        print(f"\nDraft created in Approvals/ folder")
        print("Edit the file, then move to Approved/ to post")

    elif '--test' in sys.argv or '-t' in sys.argv:
        print("Running in TEST mode - single pass")
        print("A browser window will open. Login if prompted.\n")
        asyncio.run(poster.run_once())

    else:
        print("Running continuously. Press Ctrl+C to stop.")
        print("A browser window will open. Login if prompted.\n")
        try:
            asyncio.run(poster.run())
        except KeyboardInterrupt:
            print("\n\nShutdown requested. Goodbye!")


if __name__ == '__main__':
    main()
