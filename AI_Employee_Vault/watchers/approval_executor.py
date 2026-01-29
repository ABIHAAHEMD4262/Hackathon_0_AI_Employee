"""
Approval Executor
Watches the queue folder and executes approved actions (sends emails, posts, etc.)
"""

import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from email_sender import EmailSender


class ApprovalExecutor:
    """
    Executes approved actions from the queue
    """

    def __init__(self, vault_path: str):
        load_dotenv()

        self.vault_path = Path(vault_path)
        self.queue_path = self.vault_path / '.queue'
        self.logs_path = self.vault_path / 'Logs'

        # Create folders
        self.queue_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)

        # Email sender
        self.email_sender = EmailSender()

        self.log("Approval Executor initialized")

    def log(self, message: str, level: str = 'INFO'):
        """Write to log file"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)

        today = datetime.now().strftime('%Y-%m-%d')
        log_file = self.logs_path / f'daily_{today}.log'
        with open(log_file, 'a') as f:
            f.write(log_entry + '\n')

    def parse_email_draft(self, content: str) -> dict:
        """Parse email draft markdown to extract email details"""
        result = {
            'to': None,
            'subject': None,
            'body': None
        }

        # Extract from frontmatter
        frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)

            to_match = re.search(r'to:\s*(.+)', frontmatter)
            if to_match:
                result['to'] = to_match.group(1).strip()

            subject_match = re.search(r'subject:\s*(.+)', frontmatter)
            if subject_match:
                result['subject'] = subject_match.group(1).strip()

        # Extract body - look for content between --- markers after frontmatter
        body_match = re.search(r'\*\*To:\*\*.*?\n\*\*Subject:\*\*.*?\n\n---\n\n(.*?)\n\n---', content, re.DOTALL)
        if body_match:
            result['body'] = body_match.group(1).strip()
        else:
            # Fallback - get content after "---" in the body
            parts = content.split('---')
            if len(parts) >= 4:
                result['body'] = parts[2].strip()

        return result

    def execute_email(self, queue_item: dict, approved_file: Path) -> bool:
        """Execute an approved email draft"""
        try:
            content = approved_file.read_text(encoding='utf-8')
            email_data = self.parse_email_draft(content)

            if not email_data['to'] or not email_data['subject']:
                self.log(f"Missing email details in {approved_file.name}", 'ERROR')
                return False

            # Use a default body if not found
            if not email_data['body']:
                email_data['body'] = "Thank you for your email. I will get back to you shortly."

            self.log(f"Sending email to {email_data['to']}")

            success = self.email_sender.reply_to_email(
                to=email_data['to'],
                original_subject=email_data['subject'],
                body=email_data['body']
            )

            if success:
                self.log(f"Email sent successfully to {email_data['to']}")
            else:
                self.log(f"Failed to send email to {email_data['to']}", 'ERROR')

            return success

        except Exception as e:
            self.log(f"Error executing email: {e}", 'ERROR')
            return False

    def process_queue_item(self, queue_file: Path):
        """Process a single queue item"""
        try:
            # Read queue item
            queue_data = json.loads(queue_file.read_text())
            item_id = queue_data.get('id', 'unknown')
            source_path = Path(queue_data.get('sourcePath', ''))

            self.log(f"Processing approved item: {item_id}")

            if not source_path.exists():
                self.log(f"Source file not found: {source_path}", 'ERROR')
                queue_file.unlink()
                return

            # Determine type and execute
            content = source_path.read_text(encoding='utf-8')

            if 'type: email_draft' in content or 'type: email' in content:
                success = self.execute_email(queue_data, source_path)
            elif 'type: linkedin_post' in content:
                self.log(f"LinkedIn post approved - would post: {item_id}")
                success = True  # Placeholder - LinkedIn API would go here
            elif 'type: social_post' in content:
                self.log(f"Social post approved - would post: {item_id}")
                success = True  # Placeholder - Social API would go here
            else:
                self.log(f"Unknown item type for {item_id}", 'WARNING')
                success = True

            # Remove from queue after processing
            queue_file.unlink()
            self.log(f"Removed {item_id} from queue")

        except Exception as e:
            self.log(f"Error processing queue item: {e}", 'ERROR')

    def check_queue(self):
        """Check and process all items in the queue"""
        queue_files = list(self.queue_path.glob('execute_*.json'))

        if queue_files:
            self.log(f"Found {len(queue_files)} items in queue")

            for queue_file in queue_files:
                self.process_queue_item(queue_file)

        return len(queue_files)

    def run_once(self):
        """Run a single check"""
        self.log("Checking approval queue...")
        count = self.check_queue()
        if count == 0:
            self.log("Queue is empty")

    def run(self, interval: int = 10):
        """Run continuously"""
        self.log(f"Starting Approval Executor (checking every {interval}s)")

        while True:
            try:
                self.check_queue()
            except Exception as e:
                self.log(f"Error in main loop: {e}", 'ERROR')

            time.sleep(interval)


def main():
    """Main entry point"""
    import sys

    load_dotenv()

    vault_path = os.getenv('VAULT_PATH', str(Path(__file__).parent.parent))

    print("=" * 50)
    print("  Approval Executor")
    print("=" * 50)
    print(f"Vault: {vault_path}")
    print()

    try:
        executor = ApprovalExecutor(vault_path)

        if '--test' in sys.argv or '-t' in sys.argv:
            print("Running in TEST mode - single check only\n")
            executor.run_once()
        else:
            print("Running continuously. Press Ctrl+C to stop.\n")
            executor.run()

    except KeyboardInterrupt:
        print("\n\nShutdown requested. Goodbye!")
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
