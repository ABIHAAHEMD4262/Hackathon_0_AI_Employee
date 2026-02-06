"""
Instagram Poster - Gold Tier Component
=======================================
Creates draft Instagram posts for human approval, then publishes via
the Instagram Graph API (or dry-run mode when API is not configured).

Flow:
  1. create_post_draft(topic) -> writes SOCIAL_IG_*.md to Pending_Approval/
  2. Human reviews in Obsidian / Dashboard and moves file to Approved/
  3. process_approved_posts() -> publishes via Graph API -> writes summary to Logs/SocialMedia/

Note: Instagram Graph API requires a Facebook Business account linked to
an Instagram Professional account. Image posts require a hosted image URL.
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


class InstagramPoster:
    """Posts approved content to Instagram via the Graph API."""

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

        # API credentials
        self.ig_user_id = os.getenv('INSTAGRAM_USER_ID', '')
        self.access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN', '')
        self.dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'

        self.log("Instagram Poster initialized" + (" [DRY-RUN]" if self.dry_run else ""))

    # ── Logging ─────────────────────────────────────────────────────
    def log(self, message: str, level: str = 'INFO'):
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [Instagram] [{level}] {message}"
        print(entry)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs / f'daily_{today}.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(entry + '\n')

    # ── Draft creation ──────────────────────────────────────────────
    def create_post_draft(
        self, topic: str, content: str = '',
        image_url: str = '', style: str = 'visual'
    ) -> Path:
        """Create an Instagram post draft in Pending_Approval for human review."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"SOCIAL_IG_{timestamp}.md"
        filepath = self.pending_approval / filename

        if not content:
            content = self._generate_draft_content(topic, style)

        draft = f"""---
type: instagram_post
title: Instagram Post - {topic}
status: pending_approval
platform: instagram
created: {datetime.now().isoformat()}
topic: {topic}
style: {style}
image_url: {image_url}
---

# Instagram Post Draft

**Topic:** {topic}
**Style:** {style}
**Image URL:** {image_url or '(add a hosted image URL before approving)'}

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
        return (
            f"{topic}\n\n"
            ".\n"
            ".\n"
            ".\n\n"
            "#AI #Automation #Tech #Business #Innovation #Startup"
        )

    # ── Graph API publishing ────────────────────────────────────────
    def _publish_to_instagram(self, caption: str, image_url: str) -> Dict[str, Any]:
        """Publish via the Instagram Content Publishing API (two-step)."""
        if self.dry_run or not self.access_token or not self.ig_user_id:
            self.log("DRY-RUN: Would publish to Instagram", 'INFO')
            return {'dry_run': True, 'id': f'dry_run_{int(time.time())}'}

        if not REQUESTS_AVAILABLE:
            self.log("requests library not installed", 'ERROR')
            return {'error': 'requests not installed'}

        if not image_url:
            self.log("Instagram requires an image_url for posts", 'ERROR')
            return {'error': 'image_url required'}

        # Step 1: Create media container
        container_url = f"{self.GRAPH_API_BASE}/{self.ig_user_id}/media"
        container_payload = {
            'image_url': image_url,
            'caption': caption,
            'access_token': self.access_token,
        }
        resp = requests.post(container_url, data=container_payload, timeout=30)
        resp.raise_for_status()
        container_id = resp.json().get('id')

        # Step 2: Publish the container
        publish_url = f"{self.GRAPH_API_BASE}/{self.ig_user_id}/media_publish"
        publish_payload = {
            'creation_id': container_id,
            'access_token': self.access_token,
        }
        resp2 = requests.post(publish_url, data=publish_payload, timeout=30)
        resp2.raise_for_status()
        return resp2.json()

    # ── Post parsing ────────────────────────────────────────────────
    def _parse_post_file(self, filepath: Path) -> Optional[Dict[str, str]]:
        try:
            content = filepath.read_text(encoding='utf-8')
            image_url = ''
            topic = 'Instagram Post'
            for line in content.split('\n'):
                if line.startswith('image_url:'):
                    image_url = line.split(':', 1)[1].strip()
                if line.startswith('topic:'):
                    topic = line.split(':', 1)[1].strip()

            parts = content.split('---')
            body = ''
            if len(parts) >= 4:
                body = parts[3].strip()
                body = body.replace('*This post was drafted by AI Employee.', '').strip()
                body = body.replace('*Move this file to Approved/ to publish.*', '').strip()
            elif len(parts) >= 3:
                body = parts[2].strip()

            if body:
                return {'caption': body, 'image_url': image_url, 'topic': topic}
        except Exception as e:
            self.log(f"Error parsing {filepath.name}: {e}", 'ERROR')
        return None

    # ── Summary generation ──────────────────────────────────────────
    def _write_summary(self, filename: str, topic: str, result: Dict[str, Any]):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = self.social_logs / f'instagram_summary_{ts}.md'
        post_id = result.get('id', 'unknown')

        summary = f"""---
platform: instagram
posted_at: {datetime.now().isoformat()}
post_id: {post_id}
source_file: {filename}
dry_run: {result.get('dry_run', False)}
---

# Instagram Post Summary

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
        approved_files = list(self.approved.glob('*IG*.md')) + list(self.approved.glob('*instagram*.md'))
        if not approved_files:
            return 0

        posted = 0
        for filepath in approved_files:
            data = self._parse_post_file(filepath)
            if not data:
                self.log(f"Skipping {filepath.name}: no content", 'WARNING')
                continue

            try:
                result = self._publish_to_instagram(data['caption'], data['image_url'])
                self._write_summary(filepath.name, data['topic'], result)
                dest = self.done / filepath.name
                filepath.rename(dest)
                self.log(f"Posted and archived: {filepath.name}")
                posted += 1
            except Exception as e:
                self.log(f"Failed to post {filepath.name}: {e}", 'ERROR')

        return posted

    # ── Run loops ───────────────────────────────────────────────────
    def run_once(self):
        self.log("Checking for approved Instagram posts...")
        count = self.process_approved_posts()
        self.log(f"Posted {count} Instagram items")

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
    print("  Instagram Poster - AI Employee")
    print("=" * 50)
    print(f"Vault: {vault_path}\n")

    poster = InstagramPoster(vault_path)

    if '--draft' in sys.argv:
        idx = sys.argv.index('--draft')
        topic = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "Behind the scenes"
        image_url = ''
        if '--image' in sys.argv:
            img_idx = sys.argv.index('--image')
            image_url = sys.argv[img_idx + 1] if len(sys.argv) > img_idx + 1 else ''
        poster.create_post_draft(topic, image_url=image_url)
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
