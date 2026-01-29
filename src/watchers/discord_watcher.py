"""
Discord Watcher Module
======================
Monitors Discord for messages, mentions, and DMs.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import os

from .base_watcher import BaseWatcher, Event, EventType, generate_event_id


class DiscordWatcher(BaseWatcher):
    """
    Discord message and mention watcher.

    Features:
    - Server message monitoring
    - Direct message tracking
    - Mention detection
    - Role ping detection
    - Thread monitoring

    Requires:
    - DISCORD_BOT_TOKEN environment variable
    - pip install discord.py
    """

    def __init__(
        self,
        check_interval: int = 10,
        config: Optional[Dict] = None,
        guild_ids: List[int] = None,
        channel_ids: List[int] = None
    ):
        super().__init__("Discord", check_interval, config)
        self.bot_token = os.getenv("DISCORD_BOT_TOKEN") or (config.get("bot_token") if config else None)
        self.guild_ids = guild_ids or []
        self.channel_ids = channel_ids or []

        self.client = None
        self.bot_user_id: Optional[int] = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.connected = False

        # Priority settings
        self.priority_channels: List[int] = config.get("priority_channels", []) if config else []
        self.vip_users: List[int] = config.get("vip_users", []) if config else []

    async def setup(self) -> bool:
        """Initialize Discord client."""
        try:
            import discord
            from discord.ext import commands

            if not self.bot_token:
                self.logger.warning("DISCORD_BOT_TOKEN not set. Discord watcher inactive.")
                return True

            intents = discord.Intents.default()
            intents.message_content = True
            intents.dm_messages = True

            self.client = commands.Bot(command_prefix='!', intents=intents)

            @self.client.event
            async def on_ready():
                self.bot_user_id = self.client.user.id
                self.connected = True
                self.logger.info(f"Discord connected as {self.client.user}")

            @self.client.event
            async def on_message(message):
                # Don't process own messages
                if message.author.id == self.bot_user_id:
                    return

                await self.message_queue.put({
                    'id': message.id,
                    'content': message.content,
                    'author_id': message.author.id,
                    'author_name': str(message.author),
                    'channel_id': message.channel.id,
                    'channel_name': getattr(message.channel, 'name', 'DM'),
                    'guild_id': message.guild.id if message.guild else None,
                    'guild_name': message.guild.name if message.guild else None,
                    'is_dm': isinstance(message.channel, discord.DMChannel),
                    'mentions_bot': self.client.user in message.mentions,
                    'timestamp': message.created_at.timestamp(),
                    'attachments': [a.filename for a in message.attachments],
                    'embeds': len(message.embeds) > 0
                })

            # Start bot in background
            asyncio.create_task(self._run_bot())

            # Wait for connection
            timeout = 30
            start = datetime.now()
            while not self.connected:
                if (datetime.now() - start).total_seconds() > timeout:
                    self.logger.warning("Discord connection timeout")
                    return True
                await asyncio.sleep(1)

            return True

        except ImportError:
            self.logger.warning("discord.py not installed. Run: pip install discord.py")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Discord: {e}")
            return False

    async def _run_bot(self):
        """Run Discord bot."""
        if self.client and self.bot_token:
            try:
                await self.client.start(self.bot_token)
            except Exception as e:
                self.logger.error(f"Discord bot error: {e}")

    async def check(self) -> List[Event]:
        """Check for new Discord messages."""
        events = []

        while not self.message_queue.empty():
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=0.1
                )
                event = self._create_event(message)
                events.append(event)
            except asyncio.TimeoutError:
                break

        return events

    def _create_event(self, message: Dict) -> Event:
        """Create an Event from a Discord message."""
        # Determine priority
        priority = 5

        if message.get('is_dm'):
            priority = 2
        elif message.get('mentions_bot'):
            priority = 3
        elif message.get('channel_id') in self.priority_channels:
            priority = 3
        elif message.get('author_id') in self.vip_users:
            priority = 2

        # Check urgency keywords
        content_lower = message.get('content', '').lower()
        if any(word in content_lower for word in ['urgent', 'asap', 'help', 'emergency']):
            priority = min(priority, 2)

        return Event(
            id=generate_event_id("discord", str(message.get('id', ''))),
            type=EventType.DISCORD_MESSAGE,
            source="discord",
            channel="discord",
            timestamp=datetime.fromtimestamp(message.get('timestamp', datetime.now().timestamp())),
            data={
                "message_id": message.get('id'),
                "content": message.get('content'),
                "author_id": message.get('author_id'),
                "author_name": message.get('author_name'),
                "channel_id": message.get('channel_id'),
                "channel_name": message.get('channel_name'),
                "guild_id": message.get('guild_id'),
                "guild_name": message.get('guild_name'),
                "is_dm": message.get('is_dm'),
                "mentions_bot": message.get('mentions_bot'),
                "attachments": message.get('attachments', []),
                "has_embeds": message.get('embeds', False)
            },
            priority=priority
        )

    async def send_message(self, channel_id: int, content: str) -> bool:
        """Send a Discord message (requires HITL approval)."""
        if not self.client or not self.connected:
            return False

        try:
            channel = self.client.get_channel(channel_id)
            if channel:
                await channel.send(content)
                return True
        except Exception as e:
            self.logger.error(f"Failed to send Discord message: {e}")
        return False

    async def teardown(self):
        """Clean up Discord resources."""
        if self.client:
            await self.client.close()
        self.connected = False
