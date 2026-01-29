"""
MCP Email Server - Silver Tier Component
==========================================
This MCP (Model Context Protocol) server allows Claude to SEND emails.

What is MCP?
- MCP = Model Context Protocol
- It's a way for Claude to interact with external services
- Claude can call "tools" defined in this server
- The server executes the action and returns results

How it works:
1. Claude reads an approved email draft from /Approved folder
2. Claude calls the "send_email" tool in this MCP server
3. This server sends the email via Gmail
4. Server returns success/failure to Claude
5. Claude moves the task to /Done

SETUP REQUIRED:
1. Set environment variables:
   - EMAIL_USER=your_gmail@gmail.com
   - EMAIL_PASS=your_app_password (16-char app password)
2. Enable Gmail API or use App Passwords
"""

import os
import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('MCP_EmailServer')


class EmailServer:
    """
    MCP Server for sending emails via Gmail.

    This server provides tools that Claude can call to send emails.
    All emails go through human approval first (in /Pending_Approval).
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_folder = self.vault_path / 'Logs' / 'Email'
        self.logs_folder.mkdir(parents=True, exist_ok=True)

        # Email configuration from environment
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS', '').replace(' ', '')  # Remove spaces from app password

        if not self.email_user or not self.email_pass:
            logger.warning("EMAIL_USER or EMAIL_PASS not set. Email sending will fail.")

        # Define available tools for MCP
        self.tools = {
            'send_email': self.send_email,
            'draft_email': self.draft_email,
            'list_drafts': self.list_drafts,
            'get_email_status': self.get_email_status
        }

        logger.info(f"Email Server initialized for vault: {vault_path}")

    def get_tool_definitions(self) -> list:
        """
        Return MCP tool definitions for Claude.
        This tells Claude what tools are available and how to use them.
        """
        return [
            {
                "name": "send_email",
                "description": "Send an email that has been approved. Only use after human approval.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line"
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body content (can include HTML)"
                        },
                        "reply_to": {
                            "type": "string",
                            "description": "Optional reply-to address"
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "draft_email",
                "description": "Create an email draft for human approval. Does NOT send the email.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line"
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body content"
                        },
                        "context": {
                            "type": "string",
                            "description": "Why this email is being sent (for human reviewer)"
                        }
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "list_drafts",
                "description": "List all email drafts pending approval",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_email_status",
                "description": "Check if an email was sent successfully",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "email_id": {
                            "type": "string",
                            "description": "The email ID to check"
                        }
                    },
                    "required": ["email_id"]
                }
            }
        ]

    def send_email(self, to: str, subject: str, body: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an email via Gmail SMTP.

        IMPORTANT: This should only be called AFTER human approval!

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (text or HTML)
            reply_to: Optional reply-to address

        Returns:
            Dict with success status and details
        """
        email_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        try:
            # Validate email configuration
            if not self.email_user or not self.email_pass:
                return {
                    "success": False,
                    "error": "Email credentials not configured. Set EMAIL_USER and EMAIL_PASS environment variables.",
                    "email_id": email_id
                }

            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = to
            msg['Subject'] = subject

            if reply_to:
                msg['Reply-To'] = reply_to

            # Add body (as both plain text and HTML)
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(body, 'html')
            msg.attach(text_part)
            msg.attach(html_part)

            # Send via Gmail SMTP
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_user, self.email_pass)
                server.sendmail(self.email_user, to, msg.as_string())

            # Log the sent email
            self._log_email(email_id, to, subject, body, status='sent')

            logger.info(f"Email sent successfully to {to} (ID: {email_id})")

            return {
                "success": True,
                "message": f"Email sent successfully to {to}",
                "email_id": email_id,
                "timestamp": datetime.now().isoformat()
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            self._log_email(email_id, to, subject, body, status='failed', error=str(e))
            return {
                "success": False,
                "error": "Authentication failed. Check EMAIL_USER and EMAIL_PASS (use App Password, not regular password).",
                "email_id": email_id
            }

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            self._log_email(email_id, to, subject, body, status='failed', error=str(e))
            return {
                "success": False,
                "error": str(e),
                "email_id": email_id
            }

    def draft_email(self, to: str, subject: str, body: str, context: str = "") -> Dict[str, Any]:
        """
        Create an email draft for human approval.
        This does NOT send the email - it creates a file in /Pending_Approval.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            context: Why this email is being sent

        Returns:
            Dict with draft details
        """
        draft_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        approval_folder = self.vault_path / 'Pending_Approval'
        approval_folder.mkdir(parents=True, exist_ok=True)

        draft_file = approval_folder / f'EMAIL_DRAFT_{draft_id}.md'

        content = f'''---
type: email_draft
draft_id: {draft_id}
to: {to}
subject: {subject}
created: {datetime.now().isoformat()}
status: pending_approval
---

# Email Draft - Approval Required

## Recipient
**To:** {to}

## Subject
{subject}

## Email Body

{body}

---

## Context
{context if context else "No context provided"}

---

## Actions

- [ ] **APPROVE** - Send this email
- [ ] **REJECT** - Do not send
- [ ] **EDIT** - Modify before sending

## For AI Employee

When approved:
1. Call `send_email` tool with the details above
2. Move this file to /Done
3. Log the action

When rejected:
1. Move this file to /Rejected
2. Note the reason

---

*Draft created by AI Employee at {datetime.now().strftime('%Y-%m-%d %H:%M')}*
*Awaiting human approval before sending*
'''

        draft_file.write_text(content)
        logger.info(f"Email draft created: {draft_file}")

        return {
            "success": True,
            "message": "Draft created and awaiting approval",
            "draft_id": draft_id,
            "draft_file": str(draft_file),
            "to": to,
            "subject": subject
        }

    def list_drafts(self) -> Dict[str, Any]:
        """List all email drafts pending approval."""
        approval_folder = self.vault_path / 'Pending_Approval'
        drafts = list(approval_folder.glob('EMAIL_DRAFT_*.md'))

        draft_list = []
        for draft in drafts:
            content = draft.read_text()
            # Extract basic info from frontmatter
            lines = content.split('\n')
            draft_info = {'file': draft.name}
            for line in lines[:15]:
                if line.startswith('to:'):
                    draft_info['to'] = line.split(':', 1)[1].strip()
                elif line.startswith('subject:'):
                    draft_info['subject'] = line.split(':', 1)[1].strip()
                elif line.startswith('created:'):
                    draft_info['created'] = line.split(':', 1)[1].strip()
            draft_list.append(draft_info)

        return {
            "success": True,
            "count": len(draft_list),
            "drafts": draft_list
        }

    def get_email_status(self, email_id: str) -> Dict[str, Any]:
        """Check the status of a sent email."""
        log_file = self.logs_folder / f'{email_id}.json'

        if log_file.exists():
            with open(log_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "success": False,
                "error": f"No email found with ID: {email_id}"
            }

    def _log_email(self, email_id: str, to: str, subject: str, body: str,
                   status: str, error: str = None):
        """Log email for audit trail."""
        log_file = self.logs_folder / f'{email_id}.json'

        log_data = {
            "email_id": email_id,
            "to": to,
            "subject": subject,
            "body_preview": body[:200] + "..." if len(body) > 200 else body,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "error": error
        }

        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)

        # Also append to daily log
        daily_log = self.logs_folder / f'daily_{datetime.now().strftime("%Y%m%d")}.md'
        with open(daily_log, 'a') as f:
            f.write(f"\n## Email {email_id}\n")
            f.write(f"- **Time:** {datetime.now().strftime('%H:%M:%S')}\n")
            f.write(f"- **To:** {to}\n")
            f.write(f"- **Subject:** {subject}\n")
            f.write(f"- **Status:** {status}\n")
            if error:
                f.write(f"- **Error:** {error}\n")
            f.write("\n")

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a tool call from Claude.
        This is the main entry point for MCP tool execution.
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

        tool_func = self.tools[tool_name]
        return tool_func(**arguments)


# MCP Server runner (for production use with Claude)
def run_mcp_server(vault_path: str):
    """
    Run the MCP server in standalone mode.
    In production, this would integrate with Claude's MCP protocol.
    """
    server = EmailServer(vault_path)

    print("=" * 50)
    print("MCP Email Server Started")
    print("=" * 50)
    print(f"Vault: {vault_path}")
    print(f"Email User: {server.email_user or 'NOT SET'}")
    print("\nAvailable Tools:")
    for tool in server.get_tool_definitions():
        print(f"  - {tool['name']}: {tool['description']}")
    print("=" * 50)

    # For testing: interactive mode
    while True:
        print("\nTest Commands:")
        print("  1. draft <to> <subject> - Create a draft")
        print("  2. list - List pending drafts")
        print("  3. send <to> <subject> <body> - Send email (requires approval)")
        print("  4. quit - Exit")

        try:
            cmd = input("\n> ").strip()

            if cmd.startswith('draft'):
                parts = cmd.split(' ', 2)
                if len(parts) >= 3:
                    result = server.draft_email(
                        to=parts[1],
                        subject=parts[2],
                        body="This is a test email body.",
                        context="Testing the MCP email server"
                    )
                    print(json.dumps(result, indent=2))

            elif cmd == 'list':
                result = server.list_drafts()
                print(json.dumps(result, indent=2))

            elif cmd.startswith('send'):
                parts = cmd.split(' ', 3)
                if len(parts) >= 4:
                    result = server.send_email(
                        to=parts[1],
                        subject=parts[2],
                        body=parts[3]
                    )
                    print(json.dumps(result, indent=2))

            elif cmd == 'quit':
                break

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\nMCP Email Server stopped.")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python email_server.py <vault_path>")
        sys.exit(1)

    vault_path = sys.argv[1]
    run_mcp_server(vault_path)
