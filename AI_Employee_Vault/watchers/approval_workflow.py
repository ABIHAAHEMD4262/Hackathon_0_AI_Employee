"""
Human-in-the-Loop Approval Workflow - Silver Tier Component
============================================================
This ensures humans approve sensitive actions before AI executes them.

FLOW:
1. AI creates action request in /Pending_Approval
2. Human reviews and marks as APPROVED or REJECTED
3. Watcher detects approval/rejection
4. If approved: moves to /Approved, AI can execute
5. If rejected: moves to /Rejected with reason
6. All actions logged for audit trail

WHY THIS MATTERS:
- AI doesn't send emails without your OK
- AI doesn't post to LinkedIn without your OK
- AI doesn't contact clients without your OK
- You stay in control!
"""

import time
import re
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ApprovalWorkflow')


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_EDIT = "needs_edit"


class ApprovalWorkflow:
    """
    Manages the human-in-the-loop approval process.

    Monitors /Pending_Approval folder for:
    - [x] APPROVE markers
    - [x] REJECT markers
    - Edits to content

    Then moves files to appropriate folders and triggers actions.
    """

    def __init__(self, vault_path: str, check_interval: int = 30):
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval

        # Key folders
        self.pending_folder = self.vault_path / 'Pending_Approval'
        self.approved_folder = self.vault_path / 'Approved'
        self.rejected_folder = self.vault_path / 'Rejected'
        self.done_folder = self.vault_path / 'Done'
        self.logs_folder = self.vault_path / 'Logs' / 'Approvals'

        # Create folders if they don't exist
        for folder in [self.pending_folder, self.approved_folder,
                       self.rejected_folder, self.done_folder, self.logs_folder]:
            folder.mkdir(parents=True, exist_ok=True)

        # Action handlers (registered by other components)
        self.action_handlers: Dict[str, Callable] = {}

        # Track processed files
        self.processed_files = set()

        logger.info(f"Approval Workflow initialized for vault: {vault_path}")

    def register_action_handler(self, action_type: str, handler: Callable):
        """
        Register a handler function for a specific action type.

        Example:
            workflow.register_action_handler('email_draft', email_server.send_approved_email)
        """
        self.action_handlers[action_type] = handler
        logger.info(f"Registered handler for action type: {action_type}")

    def check_for_approvals(self) -> List[Dict[str, Any]]:
        """
        Check /Pending_Approval for files that have been approved or rejected.

        Human marks approval by:
        - Checking [x] **APPROVE** in the file
        - OR checking [x] **REJECT** in the file
        """
        results = []

        pending_files = list(self.pending_folder.glob('*.md'))

        for filepath in pending_files:
            if filepath.name in self.processed_files:
                continue

            try:
                content = filepath.read_text()
                status = self._detect_approval_status(content)

                if status == ApprovalStatus.APPROVED:
                    result = self._handle_approval(filepath, content)
                    results.append(result)

                elif status == ApprovalStatus.REJECTED:
                    result = self._handle_rejection(filepath, content)
                    results.append(result)

                elif status == ApprovalStatus.NEEDS_EDIT:
                    # Keep in pending, but log that edit was requested
                    logger.info(f"Edit requested for: {filepath.name}")

                # PENDING status means no action taken yet

            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}")

        return results

    def _detect_approval_status(self, content: str) -> ApprovalStatus:
        """
        Detect if human has approved, rejected, or requested edit.

        Looks for checked boxes:
        - [x] **APPROVE** or [x] APPROVE
        - [x] **REJECT** or [x] REJECT
        - [x] **EDIT** or [x] EDIT
        """
        content_lower = content.lower()

        # Check for approval (various formats)
        approve_patterns = [
            r'\[x\]\s*\*?\*?approve\*?\*?',
            r'\[x\]\s*✅\s*approve',
            r'status:\s*approved'
        ]
        for pattern in approve_patterns:
            if re.search(pattern, content_lower):
                return ApprovalStatus.APPROVED

        # Check for rejection
        reject_patterns = [
            r'\[x\]\s*\*?\*?reject\*?\*?',
            r'\[x\]\s*❌\s*reject',
            r'status:\s*rejected'
        ]
        for pattern in reject_patterns:
            if re.search(pattern, content_lower):
                return ApprovalStatus.REJECTED

        # Check for edit request
        edit_patterns = [
            r'\[x\]\s*\*?\*?edit\*?\*?',
            r'\[x\]\s*✏️\s*edit',
            r'status:\s*needs_edit'
        ]
        for pattern in edit_patterns:
            if re.search(pattern, content_lower):
                return ApprovalStatus.NEEDS_EDIT

        return ApprovalStatus.PENDING

    def _handle_approval(self, filepath: Path, content: str) -> Dict[str, Any]:
        """Handle an approved action."""
        logger.info(f"APPROVED: {filepath.name}")

        # Extract action type from frontmatter
        action_type = self._extract_frontmatter_value(content, 'type')

        # Move to approved folder
        approved_path = self.approved_folder / filepath.name
        shutil.move(str(filepath), str(approved_path))

        # Log the approval
        self._log_action(filepath.name, 'approved', action_type)

        # Execute the action if handler is registered
        result = {
            "file": filepath.name,
            "status": "approved",
            "action_type": action_type,
            "approved_path": str(approved_path),
            "timestamp": datetime.now().isoformat()
        }

        if action_type in self.action_handlers:
            try:
                handler_result = self.action_handlers[action_type](approved_path, content)
                result["action_result"] = handler_result

                # Move to done after successful execution
                done_path = self.done_folder / filepath.name
                shutil.move(str(approved_path), str(done_path))
                result["final_path"] = str(done_path)

            except Exception as e:
                logger.error(f"Action handler failed: {e}")
                result["action_error"] = str(e)
        else:
            logger.warning(f"No handler registered for action type: {action_type}")
            result["action_result"] = "No handler - manual execution required"

        self.processed_files.add(filepath.name)
        return result

    def _handle_rejection(self, filepath: Path, content: str) -> Dict[str, Any]:
        """Handle a rejected action."""
        logger.info(f"REJECTED: {filepath.name}")

        # Extract rejection reason if provided
        reason = self._extract_rejection_reason(content)
        action_type = self._extract_frontmatter_value(content, 'type')

        # Add rejection metadata to content
        rejection_note = f"\n\n---\n**REJECTED:** {datetime.now().isoformat()}\n"
        if reason:
            rejection_note += f"**Reason:** {reason}\n"

        updated_content = content + rejection_note

        # Move to rejected folder
        rejected_path = self.rejected_folder / filepath.name
        rejected_path.write_text(updated_content)
        filepath.unlink()  # Remove from pending

        # Log the rejection
        self._log_action(filepath.name, 'rejected', action_type, reason)

        self.processed_files.add(filepath.name)

        return {
            "file": filepath.name,
            "status": "rejected",
            "action_type": action_type,
            "reason": reason,
            "rejected_path": str(rejected_path),
            "timestamp": datetime.now().isoformat()
        }

    def _extract_frontmatter_value(self, content: str, key: str) -> Optional[str]:
        """Extract a value from YAML frontmatter."""
        pattern = rf'^{key}:\s*(.+)$'
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def _extract_rejection_reason(self, content: str) -> Optional[str]:
        """Try to extract rejection reason from content."""
        # Look for common patterns
        patterns = [
            r'reason:\s*(.+)',
            r'rejection reason:\s*(.+)',
            r'rejected because:\s*(.+)',
            r'## reason\n(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _log_action(self, filename: str, status: str, action_type: str,
                    reason: str = None):
        """Log approval/rejection for audit trail."""
        log_entry = {
            "filename": filename,
            "status": status,
            "action_type": action_type,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        # Append to daily log
        daily_log = self.logs_folder / f'approvals_{datetime.now().strftime("%Y%m%d")}.md'

        with open(daily_log, 'a') as f:
            f.write(f"\n## {datetime.now().strftime('%H:%M:%S')} - {filename}\n")
            f.write(f"- **Status:** {status.upper()}\n")
            f.write(f"- **Type:** {action_type}\n")
            if reason:
                f.write(f"- **Reason:** {reason}\n")
            f.write("\n")

        logger.info(f"Logged {status} for {filename}")

    def create_approval_request(self, action_type: str, title: str,
                                content: str, suggested_actions: List[str] = None,
                                metadata: Dict[str, Any] = None) -> Path:
        """
        Create a new approval request.
        Used by other components to request human approval.

        Args:
            action_type: Type of action (email_draft, linkedin_post, etc.)
            title: Title for the request
            content: Main content to be approved
            suggested_actions: List of action descriptions
            metadata: Additional metadata for frontmatter

        Returns:
            Path to the created approval request file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{action_type.upper()}_{timestamp}.md'
        filepath = self.pending_folder / filename

        # Build frontmatter
        frontmatter = f'''---
type: {action_type}
created: {datetime.now().isoformat()}
status: pending_approval
'''
        if metadata:
            for key, value in metadata.items():
                frontmatter += f'{key}: {value}\n'
        frontmatter += '---\n\n'

        # Build content
        file_content = frontmatter
        file_content += f'# {title}\n\n'
        file_content += content
        file_content += '\n\n---\n\n'
        file_content += '## Actions\n\n'
        file_content += '- [ ] **APPROVE** - Execute this action\n'
        file_content += '- [ ] **REJECT** - Do not execute\n'
        file_content += '- [ ] **EDIT** - Modify before approving\n\n'

        if suggested_actions:
            file_content += '## What Will Happen If Approved\n\n'
            for action in suggested_actions:
                file_content += f'- {action}\n'
            file_content += '\n'

        file_content += '---\n\n'
        file_content += f'*Created by AI Employee at {datetime.now().strftime("%Y-%m-%d %H:%M")}*\n'
        file_content += '*Awaiting human approval*\n'

        filepath.write_text(file_content)
        logger.info(f"Created approval request: {filepath}")

        return filepath

    def run(self):
        """
        Run the approval workflow monitor continuously.
        """
        logger.info("Starting Approval Workflow monitor...")
        logger.info(f"Monitoring: {self.pending_folder}")
        logger.info(f"Check interval: {self.check_interval} seconds")

        while True:
            try:
                results = self.check_for_approvals()
                for result in results:
                    logger.info(f"Processed: {result}")
            except Exception as e:
                logger.error(f"Error in approval check: {e}")

            time.sleep(self.check_interval)


def demo_approval_workflow(vault_path: str):
    """
    Demonstrate the approval workflow.
    Creates sample approval requests.
    """
    workflow = ApprovalWorkflow(vault_path)

    # Create sample email draft approval
    workflow.create_approval_request(
        action_type='email_draft',
        title='Email Draft - Approval Required',
        content='''## To
client@example.com

## Subject
Project Proposal - AI Automation System

## Body
Hi,

Thank you for your interest in my AI automation services.

I've prepared a proposal for your e-commerce automation needs:

1. AI Customer Service Chatbot - $2,000
2. Order Tracking Automation - $1,500
3. Inventory Management - $1,000

Total: $4,500 (or $100/hour)

Would you like to schedule a call to discuss?

Best regards,
Syeda Abiha Ahmed
Full-Stack AI/ML Engineer
''',
        suggested_actions=[
            'Send email to client@example.com',
            'Log email in /Logs/Email',
            'Move to /Done when complete'
        ],
        metadata={
            'to': 'client@example.com',
            'subject': 'Project Proposal - AI Automation System'
        }
    )

    # Create sample LinkedIn post approval
    workflow.create_approval_request(
        action_type='linkedin_post',
        title='LinkedIn Post - Approval Required',
        content='''## Post Content

🚀 Excited to share my latest project!

Built an AI Employee system that:
✅ Monitors emails automatically
✅ Drafts responses using AI
✅ Requires human approval before sending
✅ Keeps full audit trail

This is the future of business automation - AI that works WITH you, not instead of you.

What tasks would you automate first?

#AI #Automation #Freelance #AIEngineer
''',
        suggested_actions=[
            'Post to LinkedIn profile',
            'Track engagement metrics',
            'Archive in /Marketing/LinkedIn_Posted'
        ]
    )

    print("✅ Sample approval requests created!")
    print(f"   Check: {workflow.pending_folder}")
    print("\nTo approve:")
    print("   1. Open the file in Obsidian")
    print("   2. Check [x] **APPROVE** or [x] **REJECT**")
    print("   3. Save the file")
    print("   4. Workflow will detect and process it")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python approval_workflow.py <vault_path> [--demo]")
        sys.exit(1)

    vault_path = sys.argv[1]

    if '--demo' in sys.argv:
        demo_approval_workflow(vault_path)
    else:
        workflow = ApprovalWorkflow(vault_path)
        print(f"Starting Approval Workflow for: {vault_path}")
        print("Press Ctrl+C to stop")
        workflow.run()
