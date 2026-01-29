"""
WhatsApp Watcher Module
=======================
Monitors WhatsApp for new messages using whatsapp-web.js via a Node.js bridge.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import subprocess

from .base_watcher import BaseWatcher, Event, EventType, generate_event_id


class WhatsAppWatcher(BaseWatcher):
    """
    WhatsApp message watcher using whatsapp-web.js.

    Requires:
    - Node.js installed
    - npm install whatsapp-web.js qrcode-terminal

    The watcher runs a Node.js process that connects to WhatsApp Web
    and sends messages to Python via stdout JSON.
    """

    def __init__(
        self,
        check_interval: int = 10,
        config: Optional[Dict] = None,
        session_path: str = "config/whatsapp_session"
    ):
        super().__init__("WhatsApp", check_interval, config)
        self.session_path = Path(session_path)
        self.node_process: Optional[subprocess.Popen] = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.connected = False
        self.phone_number: Optional[str] = None

        # VIP contacts for priority handling
        self.vip_contacts: List[str] = config.get("vip_contacts", []) if config else []

    async def setup(self) -> bool:
        """Initialize WhatsApp Web connection."""
        try:
            # Ensure session directory exists
            self.session_path.mkdir(parents=True, exist_ok=True)

            # Create the Node.js bridge script if it doesn't exist
            bridge_script = self.session_path.parent / "whatsapp_bridge.js"
            if not bridge_script.exists():
                self._create_bridge_script(bridge_script)

            # Start Node.js process
            self.node_process = subprocess.Popen(
                ["node", str(bridge_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Start reader task
            asyncio.create_task(self._read_node_output())

            # Wait for connection (with timeout)
            timeout = 60  # 60 seconds to scan QR
            start = datetime.now()
            while not self.connected:
                if (datetime.now() - start).total_seconds() > timeout:
                    self.logger.warning("WhatsApp connection timeout - QR code may need scanning")
                    return True  # Still return True, will retry
                await asyncio.sleep(1)

            self.logger.info(f"WhatsApp connected: {self.phone_number}")
            return True

        except FileNotFoundError:
            self.logger.error("Node.js not found. Install Node.js to use WhatsApp watcher.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to setup WhatsApp: {e}")
            return False

    def _create_bridge_script(self, path: Path):
        """Create the Node.js bridge script."""
        script = '''
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './config/whatsapp_session' }),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', (qr) => {
    console.log(JSON.stringify({ type: 'qr', data: 'Scan QR code in terminal' }));
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    const info = client.info;
    console.log(JSON.stringify({
        type: 'ready',
        data: { phone: info.wid.user, name: info.pushname }
    }));
});

client.on('message', async (message) => {
    const contact = await message.getContact();
    const chat = await message.getChat();

    console.log(JSON.stringify({
        type: 'message',
        data: {
            id: message.id._serialized,
            from: message.from,
            to: message.to,
            body: message.body,
            timestamp: message.timestamp,
            isGroup: chat.isGroup,
            groupName: chat.isGroup ? chat.name : null,
            contactName: contact.pushname || contact.name || message.from,
            hasMedia: message.hasMedia,
            type: message.type
        }
    }));
});

client.on('disconnected', (reason) => {
    console.log(JSON.stringify({ type: 'disconnected', data: reason }));
    process.exit(1);
});

client.initialize();

// Handle commands from Python
process.stdin.on('data', async (data) => {
    try {
        const command = JSON.parse(data.toString());
        if (command.action === 'send') {
            await client.sendMessage(command.to, command.message);
            console.log(JSON.stringify({ type: 'sent', data: { to: command.to, success: true } }));
        }
    } catch (e) {
        console.log(JSON.stringify({ type: 'error', data: e.message }));
    }
});
'''
        with open(path, 'w') as f:
            f.write(script)

    async def _read_node_output(self):
        """Read messages from Node.js process."""
        if not self.node_process or not self.node_process.stdout:
            return

        while self.running or not self.connected:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, self.node_process.stdout.readline
                )
                if not line:
                    break

                try:
                    data = json.loads(line.strip())

                    if data['type'] == 'ready':
                        self.connected = True
                        self.phone_number = data['data'].get('phone')

                    elif data['type'] == 'message':
                        await self.message_queue.put(data['data'])

                    elif data['type'] == 'disconnected':
                        self.connected = False
                        self.logger.warning(f"WhatsApp disconnected: {data['data']}")

                except json.JSONDecodeError:
                    pass  # Non-JSON output (like QR code)

            except Exception as e:
                self.logger.error(f"Error reading Node output: {e}")
                break

    async def check(self) -> List[Event]:
        """Check for new WhatsApp messages."""
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
        """Create an Event from a WhatsApp message."""
        sender = message.get('contactName', message.get('from', 'Unknown'))

        # Determine priority
        priority = 5
        body_lower = message.get('body', '').lower()

        # VIP check
        if any(vip in sender.lower() for vip in self.vip_contacts):
            priority = 1

        # Urgency keywords
        elif any(word in body_lower for word in ['urgent', 'asap', 'emergency', 'help']):
            priority = 2

        # Group messages are lower priority
        elif message.get('isGroup'):
            priority = 7

        return Event(
            id=generate_event_id("whatsapp", message.get('id', '')),
            type=EventType.WHATSAPP_MESSAGE,
            source="whatsapp",
            channel="whatsapp",
            timestamp=datetime.fromtimestamp(message.get('timestamp', datetime.now().timestamp())),
            data={
                "message_id": message.get('id'),
                "from": message.get('from'),
                "from_name": sender,
                "to": message.get('to'),
                "body": message.get('body'),
                "is_group": message.get('isGroup', False),
                "group_name": message.get('groupName'),
                "has_media": message.get('hasMedia', False),
                "message_type": message.get('type', 'text')
            },
            priority=priority
        )

    async def send_message(self, to: str, message: str) -> bool:
        """Send a WhatsApp message (requires approval in HITL)."""
        if not self.node_process or not self.connected:
            self.logger.error("Cannot send: WhatsApp not connected")
            return False

        try:
            command = json.dumps({"action": "send", "to": to, "message": message})
            self.node_process.stdin.write(command + "\n")
            self.node_process.stdin.flush()
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False

    async def teardown(self):
        """Clean up WhatsApp connection."""
        if self.node_process:
            self.node_process.terminate()
            try:
                self.node_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.node_process.kill()
            self.node_process = None
        self.connected = False
