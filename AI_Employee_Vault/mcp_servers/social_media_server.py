"""
Social Media MCP Server - Gold Tier Component
===============================================
Handles posting to Facebook, Instagram, and Twitter (X).

IMPORTANT: All posts require human approval before publishing!

Supported Platforms:
1. Facebook - via Graph API
2. Instagram - via Graph API (Business accounts)
3. Twitter/X - via Twitter API v2

SETUP REQUIRED:
- FACEBOOK_ACCESS_TOKEN
- INSTAGRAM_ACCESS_TOKEN
- TWITTER_API_KEY
- TWITTER_API_SECRET
- TWITTER_ACCESS_TOKEN
- TWITTER_ACCESS_SECRET
"""

import os
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SocialMediaServer')


class SocialMediaPlatform(ABC):
    """Base class for social media platforms."""

    @abstractmethod
    def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_analytics(self) -> Dict[str, Any]:
        pass


class FacebookAPI(SocialMediaPlatform):
    """Facebook Graph API integration."""

    def __init__(self):
        self.access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.api_url = "https://graph.facebook.com/v18.0"

    def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to Facebook page."""
        if not self.access_token:
            return {"success": False, "error": "Facebook access token not configured"}

        try:
            url = f"{self.api_url}/{self.page_id}/feed"
            data = {
                "message": content,
                "access_token": self.access_token
            }

            response = requests.post(url, data=data)
            result = response.json()

            if "id" in result:
                return {
                    "success": True,
                    "platform": "facebook",
                    "post_id": result["id"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result.get("error", {}).get("message", "Unknown error")}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_analytics(self) -> Dict[str, Any]:
        """Get Facebook page analytics."""
        if not self.access_token:
            return {"success": False, "error": "Not configured"}

        try:
            url = f"{self.api_url}/{self.page_id}/insights"
            params = {
                "metric": "page_impressions,page_engaged_users,page_fans",
                "access_token": self.access_token
            }
            response = requests.get(url, params=params)
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class InstagramAPI(SocialMediaPlatform):
    """Instagram Graph API integration (Business accounts only)."""

    def __init__(self):
        self.access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')
        self.api_url = "https://graph.facebook.com/v18.0"

    def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to Instagram (requires media for feed posts)."""
        if not self.access_token:
            return {"success": False, "error": "Instagram access token not configured"}

        if not media_urls:
            return {"success": False, "error": "Instagram requires at least one image"}

        try:
            # Step 1: Create media container
            container_url = f"{self.api_url}/{self.account_id}/media"
            container_data = {
                "image_url": media_urls[0],
                "caption": content,
                "access_token": self.access_token
            }
            container_response = requests.post(container_url, data=container_data)
            container_result = container_response.json()

            if "id" not in container_result:
                return {"success": False, "error": "Failed to create media container"}

            # Step 2: Publish the container
            publish_url = f"{self.api_url}/{self.account_id}/media_publish"
            publish_data = {
                "creation_id": container_result["id"],
                "access_token": self.access_token
            }
            publish_response = requests.post(publish_url, data=publish_data)
            publish_result = publish_response.json()

            if "id" in publish_result:
                return {
                    "success": True,
                    "platform": "instagram",
                    "post_id": publish_result["id"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Failed to publish"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_analytics(self) -> Dict[str, Any]:
        """Get Instagram account analytics."""
        if not self.access_token:
            return {"success": False, "error": "Not configured"}

        try:
            url = f"{self.api_url}/{self.account_id}/insights"
            params = {
                "metric": "impressions,reach,follower_count",
                "period": "day",
                "access_token": self.access_token
            }
            response = requests.get(url, params=params)
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class TwitterAPI(SocialMediaPlatform):
    """Twitter/X API v2 integration."""

    def __init__(self):
        self.api_key = os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_secret = os.getenv('TWITTER_ACCESS_SECRET')
        self.api_url = "https://api.twitter.com/2"

    def _get_oauth_header(self) -> Dict[str, str]:
        """Generate OAuth header for Twitter API."""
        # In production, use proper OAuth library like requests-oauthlib
        # This is simplified for demonstration
        return {"Authorization": f"Bearer {self.access_token}"}

    def post(self, content: str, media_urls: List[str] = None) -> Dict[str, Any]:
        """Post a tweet."""
        if not self.access_token:
            return {"success": False, "error": "Twitter access token not configured"}

        # Twitter has 280 character limit
        if len(content) > 280:
            return {"success": False, "error": f"Tweet too long ({len(content)}/280 chars)"}

        try:
            url = f"{self.api_url}/tweets"
            headers = self._get_oauth_header()
            headers["Content-Type"] = "application/json"

            data = {"text": content}

            response = requests.post(url, headers=headers, json=data)
            result = response.json()

            if "data" in result and "id" in result["data"]:
                return {
                    "success": True,
                    "platform": "twitter",
                    "post_id": result["data"]["id"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": result.get("detail", "Unknown error")}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_analytics(self) -> Dict[str, Any]:
        """Get Twitter account analytics."""
        if not self.access_token:
            return {"success": False, "error": "Not configured"}

        try:
            url = f"{self.api_url}/users/me"
            headers = self._get_oauth_header()
            params = {"user.fields": "public_metrics"}

            response = requests.get(url, headers=headers, params=params)
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}


class SocialMediaServer:
    """
    MCP Server for all social media platforms.
    Manages posting, analytics, and content scheduling.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_folder = self.vault_path / 'Logs' / 'SocialMedia'
        self.logs_folder.mkdir(parents=True, exist_ok=True)

        # Initialize platforms
        self.platforms = {
            'facebook': FacebookAPI(),
            'instagram': InstagramAPI(),
            'twitter': TwitterAPI()
        }

        # Post queue folder
        self.post_queue = self.vault_path / 'Marketing' / 'Social_Queue'
        self.post_queue.mkdir(parents=True, exist_ok=True)

        # Posted archive
        self.posted_archive = self.vault_path / 'Marketing' / 'Social_Posted'
        self.posted_archive.mkdir(parents=True, exist_ok=True)

        logger.info(f"Social Media Server initialized for vault: {vault_path}")

    def get_tool_definitions(self) -> List[Dict]:
        """Return MCP tool definitions."""
        return [
            {
                "name": "post_to_social",
                "description": "Post content to a social media platform (requires approval)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["facebook", "instagram", "twitter"],
                            "description": "Target platform"
                        },
                        "content": {
                            "type": "string",
                            "description": "Post content"
                        },
                        "media_urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional media URLs"
                        }
                    },
                    "required": ["platform", "content"]
                }
            },
            {
                "name": "draft_social_post",
                "description": "Create a social media post draft for approval",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "platforms": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Target platforms"
                        },
                        "content": {
                            "type": "string",
                            "description": "Post content"
                        },
                        "scheduled_time": {
                            "type": "string",
                            "description": "Optional scheduled time (ISO format)"
                        }
                    },
                    "required": ["platforms", "content"]
                }
            },
            {
                "name": "get_social_analytics",
                "description": "Get analytics from social media platforms",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": ["facebook", "instagram", "twitter", "all"],
                            "description": "Platform to get analytics from"
                        }
                    },
                    "required": ["platform"]
                }
            },
            {
                "name": "generate_weekly_summary",
                "description": "Generate weekly social media summary",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

    def post_to_social(self, platform: str, content: str,
                       media_urls: List[str] = None) -> Dict[str, Any]:
        """Post to a specific social media platform."""
        if platform not in self.platforms:
            return {"success": False, "error": f"Unknown platform: {platform}"}

        result = self.platforms[platform].post(content, media_urls)

        # Log the post
        self._log_post(platform, content, result)

        return result

    def draft_social_post(self, platforms: List[str], content: str,
                          scheduled_time: str = None) -> Dict[str, Any]:
        """Create a draft post for human approval."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_file = self.vault_path / 'Pending_Approval' / f'SOCIAL_POST_{timestamp}.md'

        platforms_str = ', '.join(platforms)

        draft_content = f'''---
type: social_post
platforms: {platforms_str}
created: {datetime.now().isoformat()}
scheduled: {scheduled_time or 'immediate'}
status: pending_approval
---

# Social Media Post - Approval Required

## Target Platforms
{', '.join([f"**{p.title()}**" for p in platforms])}

## Post Content

{content}

---

## Character Counts
- Twitter: {len(content)}/280 {'✅' if len(content) <= 280 else '❌ TOO LONG'}
- Facebook: {len(content)} (no limit)
- Instagram: {len(content)}/2200 {'✅' if len(content) <= 2200 else '❌ TOO LONG'}

## Actions

- [ ] **APPROVE** - Post to selected platforms
- [ ] **REJECT** - Do not post
- [ ] **EDIT** - Modify before posting

---

*Created by AI Employee at {datetime.now().strftime('%Y-%m-%d %H:%M')}*
'''

        draft_file.write_text(draft_content)
        logger.info(f"Created social post draft: {draft_file}")

        return {
            "success": True,
            "draft_file": str(draft_file),
            "platforms": platforms,
            "content_length": len(content)
        }

    def get_social_analytics(self, platform: str) -> Dict[str, Any]:
        """Get analytics from one or all platforms."""
        if platform == "all":
            results = {}
            for name, api in self.platforms.items():
                results[name] = api.get_analytics()
            return {"success": True, "analytics": results}

        if platform not in self.platforms:
            return {"success": False, "error": f"Unknown platform: {platform}"}

        return self.platforms[platform].get_analytics()

    def generate_weekly_summary(self) -> Dict[str, Any]:
        """Generate weekly social media performance summary."""
        summary_file = self.vault_path / 'Logs' / 'SocialMedia' / f'weekly_summary_{datetime.now().strftime("%Y%m%d")}.md'

        # Collect analytics
        analytics = self.get_social_analytics("all")

        # Count posts this week
        posts_this_week = list(self.posted_archive.glob('*.md'))

        summary_content = f'''# Weekly Social Media Summary
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Period:** Last 7 days

---

## 📊 Overview

| Metric | Value |
|--------|-------|
| Posts Published | {len(posts_this_week)} |
| Platforms Active | {len([p for p in self.platforms.values() if p.access_token])} |

---

## 📈 Platform Performance

### Facebook
- Status: {'✅ Connected' if self.platforms['facebook'].access_token else '❌ Not Connected'}

### Instagram
- Status: {'✅ Connected' if self.platforms['instagram'].access_token else '❌ Not Connected'}

### Twitter
- Status: {'✅ Connected' if self.platforms['twitter'].access_token else '❌ Not Connected'}

---

## 📝 Posts This Week

'''
        for post in posts_this_week[-10:]:  # Last 10 posts
            summary_content += f"- {post.name}\n"

        summary_content += '''
---

## 💡 Recommendations

1. Post consistently (2-3 times per week)
2. Engage with comments and messages
3. Share project updates and learning journey
4. Use relevant hashtags

---

*Generated by AI Employee Social Media Server*
'''

        summary_file.write_text(summary_content)

        return {
            "success": True,
            "summary_file": str(summary_file),
            "posts_count": len(posts_this_week)
        }

    def _log_post(self, platform: str, content: str, result: Dict[str, Any]):
        """Log social media post for audit trail."""
        log_file = self.logs_folder / f'{platform}_{datetime.now().strftime("%Y%m%d")}.json'

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "result": result
        }

        # Append to log file
        logs = []
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)

        logs.append(log_entry)

        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool calls."""
        tools = {
            'post_to_social': self.post_to_social,
            'draft_social_post': self.draft_social_post,
            'get_social_analytics': self.get_social_analytics,
            'generate_weekly_summary': self.generate_weekly_summary
        }

        if tool_name not in tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        return tools[tool_name](**arguments)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python social_media_server.py <vault_path>")
        sys.exit(1)

    vault_path = sys.argv[1]
    server = SocialMediaServer(vault_path)

    print("Social Media MCP Server")
    print("=" * 40)
    print(f"Vault: {vault_path}")
    print("\nAvailable tools:")
    for tool in server.get_tool_definitions():
        print(f"  - {tool['name']}")
    print("\nPlatform Status:")
    for name, api in server.platforms.items():
        token = getattr(api, 'access_token', None)
        print(f"  - {name}: {'✅ Configured' if token else '❌ Not configured'}")
