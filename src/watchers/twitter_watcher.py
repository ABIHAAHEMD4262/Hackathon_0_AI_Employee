"""
Twitter/X Watcher Module
========================
Monitors Twitter for mentions, DMs, and relevant activity.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import os

from .base_watcher import BaseWatcher, Event, EventType, generate_event_id, RateLimiter


class TwitterWatcher(BaseWatcher):
    """
    Twitter/X watcher for social media monitoring.

    Features:
    - Mention detection
    - Direct message monitoring
    - Keyword tracking
    - Reply monitoring
    - Engagement notifications

    Requires:
    - Twitter API v2 credentials
    - pip install tweepy
    """

    def __init__(
        self,
        check_interval: int = 120,
        config: Optional[Dict] = None,
        track_keywords: List[str] = None
    ):
        super().__init__("Twitter", check_interval, config)

        # API credentials
        self.bearer_token = os.getenv("TWITTER_BEARER_TOKEN") or (config.get("bearer_token") if config else None)
        self.api_key = os.getenv("TWITTER_API_KEY") or (config.get("api_key") if config else None)
        self.api_secret = os.getenv("TWITTER_API_SECRET") or (config.get("api_secret") if config else None)
        self.access_token = os.getenv("TWITTER_ACCESS_TOKEN") or (config.get("access_token") if config else None)
        self.access_secret = os.getenv("TWITTER_ACCESS_SECRET") or (config.get("access_secret") if config else None)

        self.client = None
        self.user_id: Optional[str] = None
        self.username: Optional[str] = None

        # Track seen items
        self.seen_mention_ids: set = set()
        self.seen_dm_ids: set = set()
        self.last_mention_id: Optional[str] = None

        # Keywords to track
        self.track_keywords = track_keywords or []

        # VIP accounts
        self.vip_accounts: List[str] = config.get("vip_accounts", []) if config else []

        # Rate limiting (Twitter has strict limits)
        self.rate_limiter = RateLimiter(max_calls=15, period_seconds=900)  # 15 per 15 min

    async def setup(self) -> bool:
        """Initialize Twitter client."""
        try:
            import tweepy

            if not self.bearer_token:
                self.logger.warning("Twitter credentials not set. Twitter watcher inactive.")
                return True

            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )

            # Get authenticated user info
            me = self.client.get_me()
            if me.data:
                self.user_id = me.data.id
                self.username = me.data.username
                self.logger.info(f"Twitter connected as @{self.username}")

            return True

        except ImportError:
            self.logger.warning("tweepy not installed. Run: pip install tweepy")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Twitter: {e}")
            return False

    async def check(self) -> List[Event]:
        """Check for Twitter activity."""
        events = []

        if not self.client or not self.user_id:
            return events

        try:
            # Check mentions
            mention_events = await self._check_mentions()
            events.extend(mention_events)

            # Check DMs (if credentials allow)
            if self.access_token:
                dm_events = await self._check_dms()
                events.extend(dm_events)

        except Exception as e:
            self.logger.error(f"Error checking Twitter: {e}")

        return events

    async def _check_mentions(self) -> List[Event]:
        """Check for new mentions."""
        events = []

        try:
            await self.rate_limiter.acquire()

            mentions = self.client.get_users_mentions(
                id=self.user_id,
                since_id=self.last_mention_id,
                max_results=20,
                tweet_fields=['created_at', 'author_id', 'conversation_id', 'in_reply_to_user_id'],
                expansions=['author_id']
            )

            if not mentions.data:
                return events

            # Build user lookup
            users = {}
            if mentions.includes and 'users' in mentions.includes:
                for user in mentions.includes['users']:
                    users[user.id] = {
                        'username': user.username,
                        'name': user.name
                    }

            for tweet in mentions.data:
                if str(tweet.id) in self.seen_mention_ids:
                    continue

                self.seen_mention_ids.add(str(tweet.id))

                author = users.get(tweet.author_id, {})
                username = author.get('username', 'unknown')

                # Determine priority
                priority = 4
                if username in self.vip_accounts:
                    priority = 2

                event = Event(
                    id=generate_event_id("twitter_mention", str(tweet.id)),
                    type=EventType.TWITTER_MENTION,
                    source="twitter",
                    channel="twitter",
                    timestamp=tweet.created_at or datetime.now(),
                    data={
                        "tweet_id": str(tweet.id),
                        "text": tweet.text,
                        "author_id": str(tweet.author_id),
                        "author_username": username,
                        "author_name": author.get('name', ''),
                        "conversation_id": str(tweet.conversation_id) if tweet.conversation_id else None,
                        "is_reply": tweet.in_reply_to_user_id is not None,
                        "url": f"https://twitter.com/{username}/status/{tweet.id}"
                    },
                    priority=priority
                )
                events.append(event)

                # Update last seen
                if not self.last_mention_id or int(tweet.id) > int(self.last_mention_id):
                    self.last_mention_id = str(tweet.id)

        except Exception as e:
            self.logger.error(f"Error checking mentions: {e}")

        return events

    async def _check_dms(self) -> List[Event]:
        """Check for new DMs (requires OAuth 1.0a)."""
        events = []
        # Note: DM access requires elevated API access and OAuth 1.0a
        # Implementation would go here with proper authentication
        return events

    async def post_tweet(self, text: str, reply_to: Optional[str] = None) -> bool:
        """Post a tweet (requires HITL approval)."""
        if not self.client:
            return False

        try:
            await self.rate_limiter.acquire()

            if reply_to:
                self.client.create_tweet(
                    text=text,
                    in_reply_to_tweet_id=reply_to
                )
            else:
                self.client.create_tweet(text=text)

            return True

        except Exception as e:
            self.logger.error(f"Failed to post tweet: {e}")
            return False

    async def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet."""
        if not self.client:
            return False

        try:
            await self.rate_limiter.acquire()
            self.client.like(tweet_id)
            return True
        except Exception as e:
            self.logger.error(f"Failed to like tweet: {e}")
            return False

    async def teardown(self):
        """Clean up Twitter resources."""
        self.client = None
