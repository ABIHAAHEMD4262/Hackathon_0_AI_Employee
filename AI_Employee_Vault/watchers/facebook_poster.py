"""
Facebook Poster - Gold Tier Component
======================================
Creates draft Facebook posts for human approval, then publishes via
the Facebook Graph API (or dry-run mode when API is not configured).

Flow:
  1. create_post_draft(topic) -> writes SOCIAL_FB_*.md to Pending_Approval/
  2. Human reviews in Obsidian / Dashboard and moves file to Approved/
  3. process_approved_posts() -> publishes via Graph API -> writes summary to Logs/SocialMedia/
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class FacebookPoster:
    """Posts approved content to Facebook via the Graph API."""

    GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

    def __init__(self, vault_path: str):
        load_dotenv()

        self.vault_path = Path(vault_path)
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.logs = self.vault_path / 'Logs'
        self.social_logs = self.logs / 'SocialMedia'

        for folder in [self.pending_approval, self.approved, self.done, self.social_logs]:
            folder.mkdir(parents=True, exist_ok=True)

        # API credentials from env
        self.page_id = os.getenv('FACEBOOK_PAGE_ID', '')
        self.access_token = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'

        self.log("Facebook Poster initialized" + (" [DRY-RUN]" if self.dry_run else ""))

    # ── Logging ─────────────────────────────────────────────────────
    def log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [Facebook] [{level}] {message}"
        print(entry)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'daily_{today}.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(entry + '\n')

    # ── Draft creation ──────────────────────────────────────────────
    def create_post_draft(self, topic: str, content: str = '', style: str = 'engaging') -> Path:
        """Create a Facebook post draft in Pending_Approval for human review."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"SOCIAL_FB_{timestamp}.md"
        filepath = self.pending_approval / filename

        if not content:
            content = self._generate_draft_content(topic, style)

        draft = f"""---
type: facebook_post
title: Facebook Post - {topic}
status: pending_approval
platform: facebook
created: {datetime.now().isoformat()}
topic: {topic}
style: {style}
---

# Facebook Post Draft

**Topic:** {topic}
**Style:** {style}

---

{content}

---

*This post was drafted by AI Employee. Review and edit before approving.*
*Move this file to Approved/ to publish.*
"""
        filepath.write_text(draft, encoding='utf-8')
        self.log(f"Draft created: {filename}")
        return filepath

    def _generate_draft_content(self, topic: str, style: str) -> str:
        if style == 'engaging':
            return (
                f"{topic}\n\n"
                "Here's what we've been working on and why it matters.\n\n"
                "Key highlights:\n"
                "- Point 1\n"
                "- Point 2\n"
                "- Point 3\n\n"
                "What do you think? Drop a comment below!\n\n"
                "#AI #Automation #Business"
            )
        return f"{topic}\n\n#AI #Business"

    # ── Graph API publishing ────────────────────────────────────────
    def _publish_to_facebook(self, text: str) -> Dict[str, Any]:
        """Publish a post via the Facebook Graph API."""
        if self.dry_run or not self.access_token or not self.page_id:
            self.log("DRY-RUN: Would publish to Facebook", 'INFO')
            return {'dry_run': True, 'id': f'dry_run_{int(time.time())}'}

        if not REQUESTS_AVAILABLE:
            self.log("requests library not installed", 'ERROR')
            return {'error': 'requests not installed'}

        url = f"{self.GRAPH_API_BASE}/{self.page_id}/feed"
        payload = {'message': text, 'access_token': self.access_token}

        resp = requests.post(url, data=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # ── Post parsing ────────────────────────────────────────────────
    def _parse_post_file(self, filepath: Path) -> Optional[str]:
        """Extract post body from an approved markdown file."""
        try:
            content = filepath.read_text(encoding='utf-8')
            parts = content.split('---')
            if len(parts) >= 4:
                body = parts[3].strip()
                body = body.replace('*This post was drafted by AI Employee.', '').strip()
                body = body.replace('*Move this file to Approved/ to publish.*', '').strip()
                if body:
                    return body
            if len(parts) >= 3:
                return parts[2].strip()
        except Exception as e:
            self.log(f"Error parsing {filepath.name}: {e}", 'ERROR')
        return None

    # ── Summary generation ──────────────────────────────────────────
    def _write_summary(self, filename: str, topic: str, result: Dict[str, Any]):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = self.social_logs / f'facebook_summary_{ts}.md'
        post_id = result.get('id', 'unknown')

        summary = f"""---
platform: facebook
posted_at: {datetime.now().isoformat()}
post_id: {post_id}
source_file: {filename}
dry_run: {result.get('dry_run', False)}
---

# Facebook Post Summary

**Posted:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Topic:** {topic}
**Post ID:** {post_id}
**Status:** {'Dry-run (simulated)' if result.get('dry_run') else 'Published'}

---

*Logged by AI Employee*
"""
        summary_file.write_text(summary, encoding='utf-8')
        self.log(f"Summary written: {summary_file.name}")

    # ── Process approved posts ──────────────────────────────────────
    def process_approved_posts(self) -> int:
        """Find approved Facebook posts and publish them."""
        approved_files = list(self.approved.glob('*FB*.md')) + list(self.approved.glob('*facebook*.md'))
        if not approved_files:
            return 0

        posted = 0
        for filepath in approved_files:
            body = self._parse_post_file(filepath)
            if not body:
                self.log(f"Skipping {filepath.name}: no content", 'WARNING')
                continue

            # Extract topic from frontmatter
            content = filepath.read_text(encoding='utf-8')
            topic = 'Facebook Post'
            for line in content.split('\n'):
                if line.startswith('topic:'):
                    topic = line.split(':', 1)[1].strip()
                    break

            try:
                result = self._publish_to_facebook(body)
                self._write_summary(filepath.name, topic, result)

                # Move to Done
                dest = self.done / filepath.name
                filepath.rename(dest)
                self.log(f"Posted and archived: {filepath.name}")
                posted += 1
            except Exception as e:
                self.log(f"Failed to post {filepath.name}: {e}", 'ERROR')

        return posted

    # ── Run loops ───────────────────────────────────────────────────
    def run_once(self):
        self.log("Checking for approved Facebook posts...")
        count = self.process_approved_posts()
        self.log(f"Posted {count} Facebook items")

    def run(self, interval: int = 300):
        self.log(f"Running continuously (every {interval}s). Ctrl+C to stop.")
        while True:
            try:
                self.process_approved_posts()
            except Exception as e:
                self.log(f"Error in loop: {e}", 'ERROR')
            time.sleep(interval)


def main():
    import sys
    load_dotenv()

    vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent))

    print("=" * 50)
    print("  Facebook Poster - AI Employee")
    print("=" * 50)
    print(f"Vault: {vault_path}\n")

    poster = FacebookPoster(vault_path)

    if '--draft' in sys.argv:
        idx = sys.argv.index('--draft')
        topic = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "Latest business update"
        poster.create_post_draft(topic)
        print(f"\nDraft created in Pending_Approval/")
        print("Review, edit, then move to Approved/ to post.")
    elif '--test' in sys.argv or '-t' in sys.argv:
        poster.run_once()
    else:
        try:
            poster.run()
        except KeyboardInterrupt:
            print("\nShutdown. Goodbye!")


if __name__ == '__main__':
    main()
