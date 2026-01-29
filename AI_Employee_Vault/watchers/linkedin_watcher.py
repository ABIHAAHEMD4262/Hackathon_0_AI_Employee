"""
LinkedIn Watcher - Silver Tier Component
==========================================
Monitors LinkedIn for:
1. New messages/connection requests
2. Post engagement notifications
3. Job opportunities mentioning your skills

Also handles AUTO-POSTING to generate leads.

How it works:
1. Uses LinkedIn API (or web scraping as fallback)
2. Checks for new notifications every 5 minutes
3. Creates action files in /Needs_Action/LinkedIn/
4. Can auto-post content from /Marketing/LinkedIn_Queue/
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

# Import base watcher
import sys
sys.path.append(str(Path(__file__).parent))
from base_watcher import BaseWatcher


class LinkedInWatcher(BaseWatcher):
    """
    Monitors LinkedIn and handles auto-posting.

    SETUP REQUIRED:
    1. Get LinkedIn API credentials (or use browser automation)
    2. Set environment variables:
       - LINKEDIN_EMAIL
       - LINKEDIN_PASSWORD
       - LINKEDIN_ACCESS_TOKEN (if using API)
    """

    def __init__(self, vault_path: str, credentials_path: Optional[str] = None):
        super().__init__(vault_path, check_interval=300)  # Check every 5 minutes

        # LinkedIn-specific folders
        self.linkedin_inbox = self.needs_action / 'LinkedIn'
        self.linkedin_inbox.mkdir(parents=True, exist_ok=True)

        # Queue for auto-posting
        self.post_queue = self.vault_path / 'Marketing' / 'LinkedIn_Queue'
        self.post_queue.mkdir(parents=True, exist_ok=True)

        # Posted content archive
        self.posted_archive = self.vault_path / 'Marketing' / 'LinkedIn_Posted'
        self.posted_archive.mkdir(parents=True, exist_ok=True)

        # Keywords to flag as important
        self.priority_keywords = [
            'job', 'opportunity', 'project', 'freelance', 'hire',
            'ai', 'automation', 'developer', 'engineer',
            'urgent', 'asap', 'interested', 'proposal',
            'kubernetes', 'fastapi', 'next.js', 'python'
        ]

        # Load credentials if provided
        self.credentials_path = Path(credentials_path) if credentials_path else None
        self.access_token = None

        self.logger.info("LinkedIn Watcher initialized")
        self.logger.info(f"LinkedIn inbox: {self.linkedin_inbox}")
        self.logger.info(f"Post queue: {self.post_queue}")

    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check LinkedIn for new notifications/messages.
        Returns list of items to process.
        """
        updates = []

        try:
            # Method 1: Use LinkedIn API (if access token available)
            if self.access_token:
                updates.extend(self._check_via_api())
            else:
                # Method 2: Simulate checking (for demo/testing)
                # In production, you'd use browser automation with Playwright
                self.logger.info("No API token - running in demo mode")
                updates.extend(self._check_demo_mode())

            # Also check if there are posts to publish
            self._check_post_queue()

        except Exception as e:
            self.logger.error(f"Error checking LinkedIn: {e}")

        return updates

    def _check_via_api(self) -> List[Dict[str, Any]]:
        """
        Check LinkedIn using official API.
        Requires LinkedIn API access (apply at LinkedIn Developer Portal).
        """
        # LinkedIn API endpoints would go here
        # This is a placeholder - actual implementation requires API approval

        """
        Example API calls:

        # Get notifications
        GET https://api.linkedin.com/v2/socialActions/{urn}/comments

        # Get messages
        GET https://api.linkedin.com/v2/messages

        # Post content
        POST https://api.linkedin.com/v2/ugcPosts
        """

        return []

    def _check_demo_mode(self) -> List[Dict[str, Any]]:
        """
        Demo mode - simulates LinkedIn notifications.
        Replace with actual LinkedIn checking in production.
        """
        # Check if there's a demo_notifications.json file for testing
        demo_file = self.vault_path / 'watchers' / 'demo_linkedin_notifications.json'

        if demo_file.exists():
            try:
                with open(demo_file, 'r') as f:
                    notifications = json.load(f)

                # Process and clear the demo file
                demo_file.unlink()  # Delete after reading
                return notifications
            except Exception as e:
                self.logger.error(f"Error reading demo file: {e}")

        return []

    def _check_post_queue(self):
        """
        Check if there are scheduled posts to publish.
        Posts are markdown files in /Marketing/LinkedIn_Queue/
        """
        queue_files = list(self.post_queue.glob('*.md'))

        for post_file in queue_files:
            try:
                content = post_file.read_text()
                frontmatter, body = self._parse_frontmatter(content)

                # Check if it's time to post
                scheduled_time = frontmatter.get('scheduled', None)
                if scheduled_time:
                    scheduled_dt = datetime.fromisoformat(scheduled_time)
                    if datetime.now() < scheduled_dt:
                        continue  # Not time yet

                # Create approval request for the post
                self._create_post_approval_request(post_file, frontmatter, body)

            except Exception as e:
                self.logger.error(f"Error processing post {post_file}: {e}")

    def _create_post_approval_request(self, post_file: Path, frontmatter: dict, body: str):
        """
        Create an approval request for a LinkedIn post.
        Human must approve before AI posts.
        """
        approval_folder = self.vault_path / 'Pending_Approval'
        approval_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        approval_file = approval_folder / f'LINKEDIN_POST_{timestamp}.md'

        content = f'''---
type: linkedin_post
source_file: {post_file.name}
created: {datetime.now().isoformat()}
status: pending_approval
action_required: approve_or_reject
---

# LinkedIn Post - Approval Required

## Post Content Preview:

{body}

---

## Actions

- [ ] **APPROVE** - Post this to LinkedIn
- [ ] **REJECT** - Do not post, move to rejected
- [ ] **EDIT** - Modify before posting

## Instructions for AI Employee:

1. If approved, post to LinkedIn and move to /Done
2. If rejected, move to /Rejected with reason
3. If edit requested, update content and re-submit for approval

---

*Created by LinkedIn Watcher - Awaiting human approval*
'''

        approval_file.write_text(content)
        self.logger.info(f"Created post approval request: {approval_file}")

    def _parse_frontmatter(self, content: str) -> tuple:
        """Parse YAML frontmatter from markdown content."""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                body = parts[2].strip()

                # Simple YAML parsing
                frontmatter = {}
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()

                return frontmatter, body

        return {}, content

    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create action file for LinkedIn notification.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        item_type = item.get('type', 'notification')
        item_id = item.get('id', timestamp)

        # Determine priority based on keywords
        text_content = str(item.get('content', '') + item.get('message', '')).lower()
        priority = 'high' if any(kw in text_content for kw in self.priority_keywords) else 'normal'

        # Create the action file
        filename = f"LINKEDIN_{item_type.upper()}_{item_id}.md"
        filepath = self.linkedin_inbox / filename

        content = self._generate_frontmatter({
            'type': f'linkedin_{item_type}',
            'from': item.get('from', 'Unknown'),
            'received': datetime.now().isoformat(),
            'priority': priority,
            'status': 'pending',
            'linkedin_id': item_id
        })

        content += f'''
# LinkedIn {item_type.title()}

## From
**{item.get('from', 'Unknown')}**
{item.get('title', '')}

## Content
{item.get('content', item.get('message', 'No content'))}

---

## Suggested Actions

'''

        # Add suggested actions based on type
        if item_type == 'message':
            content += '''- [ ] Reply to message
- [ ] Schedule follow-up
- [ ] Add to CRM/Clients folder
'''
        elif item_type == 'connection':
            content += '''- [ ] Accept connection request
- [ ] Send welcome message
- [ ] Review their profile
'''
        elif item_type == 'job':
            content += '''- [ ] Review job details
- [ ] Check if matches my skills
- [ ] Prepare application/proposal
'''
        else:
            content += '''- [ ] Review notification
- [ ] Take appropriate action
- [ ] Archive after processing
'''

        content += f'''
---

*Detected by LinkedIn Watcher at {datetime.now().strftime('%Y-%m-%d %H:%M')}*
'''

        filepath.write_text(content)
        self.mark_processed(item_id)
        self.logger.info(f"Created action file: {filepath}")

        return filepath

    def create_linkedin_post(self, content: str, scheduled_time: Optional[str] = None) -> Path:
        """
        Create a LinkedIn post file in the queue.

        Args:
            content: The post content (text)
            scheduled_time: ISO format datetime string for scheduling

        Returns:
            Path to the created post file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"POST_{timestamp}.md"
        filepath = self.post_queue / filename

        post_content = f'''---
type: linkedin_post
created: {datetime.now().isoformat()}
scheduled: {scheduled_time or 'immediate'}
status: queued
author: Syeda Abiha Ahmed
---

{content}

---

## Post Metadata

- **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Scheduled:** {scheduled_time or 'Post immediately when approved'}
- **Status:** Awaiting approval

## Hashtags to Consider

#AI #MachineLearning #FullStackDeveloper #Freelance #Automation #Kubernetes #Python #NextJS

---

*Generated by AI Employee - Edit as needed before approval*
'''

        filepath.write_text(post_content)
        self.logger.info(f"Created LinkedIn post in queue: {filepath}")

        return filepath


# Example LinkedIn post templates
LINKEDIN_POST_TEMPLATES = {
    'project_showcase': '''
🚀 Excited to share my latest project: {project_name}!

{description}

Tech Stack: {tech_stack}

Key Features:
{features}

Check it out: {link}

#AI #Development #Project #Tech
''',

    'learning_journey': '''
📚 Learning Update!

This week I've been diving deep into {topic}.

Key takeaways:
{takeaways}

Building in public is amazing for accountability! 💪

What are you learning this week?

#LearningInPublic #Developer #Growth
''',

    'availability': '''
👋 Open for new projects!

I specialize in:
✅ AI-Powered Applications (RAG chatbots, NLP systems)
✅ Full-Stack Development (Next.js, FastAPI)
✅ E-Commerce Automation
✅ Cloud-Native Deployment (Docker, Kubernetes)

Let's connect if you need help bringing your ideas to life! 🚀

DM me or email: abihaahmed413@gmail.com

#Freelance #AIEngineer #OpenForWork
'''
}


def create_sample_posts(vault_path: str):
    """
    Create sample LinkedIn posts for testing.
    These go in the queue for approval.
    """
    watcher = LinkedInWatcher(vault_path)

    # Sample post 1: Project showcase
    post1 = LINKEDIN_POST_TEMPLATES['project_showcase'].format(
        project_name='Taskley - AI-Powered Task Management',
        description='Built a full-stack task management system with AI chatbot that understands natural language commands!',
        tech_stack='Next.js 16, FastAPI, Kubernetes, OpenAI',
        features='• NLP-based task creation\n• Kubernetes auto-scaling\n• Real-time sync',
        link='https://taskley.vercel.app'
    )
    watcher.create_linkedin_post(post1)

    # Sample post 2: Availability
    post2 = LINKEDIN_POST_TEMPLATES['availability']
    watcher.create_linkedin_post(post2)

    print("Sample posts created in Marketing/LinkedIn_Queue/")


if __name__ == '__main__':
    # For testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python linkedin_watcher.py <vault_path> [--create-samples]")
        sys.exit(1)

    vault_path = sys.argv[1]

    if '--create-samples' in sys.argv:
        create_sample_posts(vault_path)
    else:
        # Run the watcher
        watcher = LinkedInWatcher(vault_path)
        print(f"Starting LinkedIn Watcher for vault: {vault_path}")
        print("Press Ctrl+C to stop")
        watcher.run()
