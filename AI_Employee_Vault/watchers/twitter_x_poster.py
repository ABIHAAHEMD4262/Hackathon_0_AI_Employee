"""
Twitter/X Poster - Gold Tier Component
=======================================
Creates draft tweets for human approval, then publishes via the
Twitter API v2 (or dry-run mode when API is not configured).

Flow:
  1. create_post_draft(topic) -> writes SOCIAL_TW_*.md to Pending_Approval/
  2. Human reviews in Obsidian / Dashboard and moves file to Approved/
  3. process_approved_posts() -> publishes via Twitter API v2 -> writes summary to Logs/SocialMedia/
"""

import os
import json
import time
import hashlib
import hmac
import base64
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

try:
    import requests
    from requests_oauthlib import OAuth1
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

try:
    import requests as _req
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class TwitterXPoster:
    """Posts approved content to Twitter/X via the v2 API."""

    API_BASE = "https://api.twitter.com/2"

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

        # Twitter API v2 credentials
        self.api_key = os.getenv('TWITTER_API_KEY', '')
        self.api_secret = os.getenv('TWITTER_API_SECRET', '')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN', '')
        self.access_secret = os.getenv('TWITTER_ACCESS_SECRET', '')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'

        self.log("Twitter/X Poster initialized" + (" [DRY-RUN]" if self.dry_run else ""))

    # ── Logging ─────────────────────────────────────────────────────
    def log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [Twitter] [{level}] {message}"
        print(entry)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'daily_{today}.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(entry + '\n')

    # ── Draft creation ──────────────────────────────────────────────
    def create_post_draft(self, topic: str, content: str = '', style: str = 'concise') -> Path:
        """Create a tweet draft in Pending_Approval for human review."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"SOCIAL_TW_{timestamp}.md"
        filepath = self.pending_approval / filename

        if not content:
            content = self._generate_draft_content(topic, style)

        draft = f"""---
type: twitter_post
title: Tweet - {topic}
status: pending_approval
platform: twitter
created: {datetime.now().isoformat()}
topic: {topic}
style: {style}
char_count: {len(content)}
---

# Tweet Draft

**Topic:** {topic}
**Characters:** {len(content)}/280

---

{content}

---

*This tweet was drafted by AI Employee. Review and edit before approving.*
*Move this file to Approved/ to publish.*
"""
        filepath.write_text(draft, encoding='utf-8')
        self.log(f"Draft created: {filename} ({len(content)} chars)")
        return filepath

    def _generate_draft_content(self, topic: str, style: str) -> str:
        base = f"{topic}"
        if style == 'concise':
            tweet = f"{base}\n\n#AI #Tech"
        elif style == 'thread':
            tweet = f"🧵 Thread: {base}\n\n1/ Key insight here"
        else:
            tweet = base

        # Enforce 280 char limit
        if len(tweet) > 280:
            tweet = tweet[:277] + '...'
        return tweet

    # ── Twitter API v2 publishing ───────────────────────────────────
    def _publish_to_twitter(self, text: str) -> Dict[str, Any]:
        """Publish a tweet via the Twitter API v2."""
        if self.dry_run or not self.api_key:
            self.log("DRY-RUN: Would publish tweet", 'INFO')
            return {'dry_run': True, 'data': {'id': f'dry_run_{int(time.time())}'}}

        if not REQUESTS_AVAILABLE:
            self.log("requests library not installed", 'ERROR')
            return {'error': 'requests not installed'}

        url = f"{self.API_BASE}/tweets"
        payload = json.dumps({'text': text})
        headers = {'Content-Type': 'application/json'}

        # Use OAuth 1.0a if available
        if OAUTH_AVAILABLE and self.access_token and self.access_secret:
            auth = OAuth1(
                self.api_key, self.api_secret,
                self.access_token, self.access_secret
            )
            resp = requests.post(url, data=payload, headers=headers, auth=auth, timeout=30)
        elif self.bearer_token:
            headers['Authorization'] = f'Bearer {self.bearer_token}'
            resp = requests.post(url, data=payload, headers=headers, timeout=30)
        else:
            self.log("No valid Twitter credentials configured", 'ERROR')
            return {'error': 'no credentials'}

        resp.raise_for_status()
        return resp.json()

    # ── Post parsing ────────────────────────────────────────────────
    def _parse_post_file(self, filepath: Path) -> Optional[Dict[str, str]]:
        try:
            content = filepath.read_text(encoding='utf-8')
            topic = 'Tweet'
            for line in content.split('\n'):
                if line.startswith('topic:'):
                    topic = line.split(':', 1)[1].strip()
                    break

            parts = content.split('---')
            body = ''
            if len(parts) >= 4:
                body = parts[3].strip()
                body = body.replace('*This tweet was drafted by AI Employee.', '').strip()
                body = body.replace('*Move this file to Approved/ to publish.*', '').strip()
            elif len(parts) >= 3:
                body = parts[2].strip()

            if body:
                # Enforce 280 limit
                if len(body) > 280:
                    body = body[:277] + '...'
                return {'text': body, 'topic': topic}
        except Exception as e:
            self.log(f"Error parsing {filepath.name}: {e}", 'ERROR')
        return None

    # ── Summary generation ──────────────────────────────────────────
    def _write_summary(self, filename: str, topic: str, result: Dict[str, Any]):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = self.social_logs / f'twitter_summary_{ts}.md'
        tweet_data = result.get('data', {})
        tweet_id = tweet_data.get('id', result.get('id', 'unknown'))

        summary = f"""---
platform: twitter
posted_at: {datetime.now().isoformat()}
tweet_id: {tweet_id}
source_file: {filename}
dry_run: {result.get('dry_run', False)}
---

# Twitter Post Summary

**Posted:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Topic:** {topic}
**Tweet ID:** {tweet_id}
**Status:** {'Dry-run (simulated)' if result.get('dry_run') else 'Published'}

---

*Logged by AI Employee*
"""
        summary_file.write_text(summary, encoding='utf-8')
        self.log(f"Summary written: {summary_file.name}")

    # ── Process approved posts ──────────────────────────────────────
    def process_approved_posts(self) -> int:
        approved_files = (
            list(self.approved.glob('*TW*.md'))
            + list(self.approved.glob('*twitter*.md'))
        )
        if not approved_files:
            return 0

        posted = 0
        for filepath in approved_files:
            data = self._parse_post_file(filepath)
            if not data:
                self.log(f"Skipping {filepath.name}: no content", 'WARNING')
                continue

            try:
                result = self._publish_to_twitter(data['text'])
                self._write_summary(filepath.name, data['topic'], result)
                dest = self.done / filepath.name
                filepath.rename(dest)
                self.log(f"Tweeted and archived: {filepath.name}")
                posted += 1
            except Exception as e:
                self.log(f"Failed to tweet {filepath.name}: {e}", 'ERROR')

        return posted

    # ── Run loops ───────────────────────────────────────────────────
    def run_once(self):
        self.log("Checking for approved tweets...")
        count = self.process_approved_posts()
        self.log(f"Posted {count} tweets")

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
    print("  Twitter/X Poster - AI Employee")
    print("=" * 50)
    print(f"Vault: {vault_path}\n")

    poster = TwitterXPoster(vault_path)

    if '--draft' in sys.argv:
        idx = sys.argv.index('--draft')
        topic = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "AI automation insights"
        poster.create_post_draft(topic)
        print(f"\nDraft created in Pending_Approval/")
    elif '--test' in sys.argv or '-t' in sys.argv:
        poster.run_once()
    else:
        try:
            poster.run()
        except KeyboardInterrupt:
            print("\nShutdown. Goodbye!")


if __name__ == '__main__':
    main()
