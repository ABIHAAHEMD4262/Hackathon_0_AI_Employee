"""
Email Sender
Sends approved email replies via Gmail SMTP
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


class EmailSender:
    """
    Sends emails via Gmail SMTP
    """

    def __init__(self):
        load_dotenv()

        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS', '').replace(' ', '')

        if not self.email_user or not self.email_pass:
            raise ValueError("Missing EMAIL_USER or EMAIL_PASS in .env")

        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587

    def send_email(self, to: str, subject: str, body: str, html: bool = False) -> bool:
        """
        Send an email

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            html: If True, send as HTML email

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = to
            msg['Subject'] = subject

            # Attach body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))

            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_pass)
                server.send_message(msg)

            print(f"[SUCCESS] Email sent to {to}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to send email: {e}")
            return False

    def reply_to_email(self, to: str, original_subject: str, body: str) -> bool:
        """
        Send a reply email (adds Re: prefix if not present)
        """
        subject = original_subject if original_subject.startswith('Re:') else f"Re: {original_subject}"
        return self.send_email(to, subject, body)


def send_reply(to: str, subject: str, message: str) -> bool:
    """
    Simple function to send a reply email

    Args:
        to: Recipient email
        subject: Original subject (Re: will be added)
        message: Reply message

    Returns:
        True if sent, False if failed
    """
    try:
        sender = EmailSender()
        return sender.reply_to_email(to, subject, message)
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Test email sending"""
    import sys

    if len(sys.argv) < 4:
        print("Usage: python email_sender.py <to> <subject> <message>")
        print("Example: python email_sender.py test@example.com 'Hello' 'This is a test'")
        sys.exit(1)

    to = sys.argv[1]
    subject = sys.argv[2]
    message = sys.argv[3]

    print(f"Sending email to: {to}")
    print(f"Subject: {subject}")
    print(f"Message: {message[:100]}...")
    print()

    success = send_reply(to, subject, message)

    if success:
        print("\n✅ Email sent successfully!")
    else:
        print("\n❌ Failed to send email")
        sys.exit(1)


if __name__ == '__main__':
    main()
