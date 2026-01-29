#!/usr/bin/env python3
"""
Gmail Connection Test for AI Employee
Uses App Password for authentication (simpler than OAuth)
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dotenv import load_dotenv
import os

# Load credentials
env_path = Path(__file__).parent.parent / "config" / "credentials" / ".env"
load_dotenv(env_path)

GMAIL_USER = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()

def test_gmail_read():
    """Test reading emails via IMAP."""
    print("\n" + "="*50)
    print("  Testing Gmail READ (IMAP)")
    print("="*50)

    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        print(f"\n Connected as: {GMAIL_USER}")

        # Select inbox
        mail.select("INBOX")

        # Get all emails
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        total_emails = len(email_ids)
        print(f" Total emails in inbox: {total_emails}")

        # Get unread emails
        status, unread = mail.search(None, "UNSEEN")
        unread_ids = unread[0].split()
        print(f" Unread emails: {len(unread_ids)}")

        # Fetch last 5 emails
        print("\n Recent emails:")
        print("-"*50)

        for i, email_id in enumerate(email_ids[-5:][::-1]):
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject = msg["Subject"] or "No Subject"
            sender = msg["From"] or "Unknown"
            date = msg["Date"] or "Unknown"

            # Decode subject if needed
            if subject.startswith("=?"):
                try:
                    decoded = email.header.decode_header(subject)
                    subject = decoded[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                except:
                    pass

            print(f"\n {i+1}. {subject[:50]}")
            print(f"    From: {sender[:40]}")
            print(f"    Date: {date[:30]}")

        mail.logout()
        print("\n" + "-"*50)
        print(" Gmail READ test PASSED!")
        return True

    except Exception as e:
        print(f"\n ERROR: {e}")
        return False

def test_gmail_send(test_mode=True):
    """Test sending emails via SMTP."""
    print("\n" + "="*50)
    print("  Testing Gmail SEND (SMTP)")
    print("="*50)

    try:
        # Connect to Gmail SMTP
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        print(f"\n Connected to SMTP server")
        print(f" Authenticated as: {GMAIL_USER}")

        if test_mode:
            print("\n [Test Mode] Not sending actual email")
            print(" To send a test email, call: test_gmail_send(test_mode=False)")
        else:
            # Create test email
            msg = MIMEMultipart()
            msg["From"] = GMAIL_USER
            msg["To"] = GMAIL_USER  # Send to self
            msg["Subject"] = "AI Employee Test - Gmail Connected!"

            body = """
Hello!

This is a test email from your AI Employee system.

If you're reading this, Gmail is properly configured and working!

Your AI Employee can now:
- Read your emails
- Draft responses
- Send emails (with your approval)

Best regards,
AI Employee Bot
            """
            msg.attach(MIMEText(body, "plain"))

            server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
            print("\n Test email sent to yourself!")

        server.quit()
        print("\n" + "-"*50)
        print(" Gmail SEND test PASSED!")
        return True

    except Exception as e:
        print(f"\n ERROR: {e}")
        return False

def get_recent_emails(count=10):
    """Get recent emails for the dashboard."""
    emails = []

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()

        for email_id in email_ids[-count:][::-1]:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            subject = msg["Subject"] or "No Subject"
            sender = msg["From"] or "Unknown"
            date = msg["Date"] or "Unknown"

            # Decode subject
            if subject.startswith("=?"):
                try:
                    decoded = email.header.decode_header(subject)
                    subject = decoded[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode()
                except:
                    pass

            # Get body preview
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")[:200]
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")[:200]

            emails.append({
                "id": email_id.decode(),
                "subject": subject[:100],
                "from": sender[:50],
                "date": date,
                "preview": body[:150]
            })

        mail.logout()

    except Exception as e:
        print(f"Error fetching emails: {e}")

    return emails

def main():
    """Run all Gmail tests."""
    print("\n" + "="*50)
    print("  AI EMPLOYEE - Gmail Connection Test")
    print("="*50)

    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("\n ERROR: Gmail credentials not found!")
        print(f" Please check: {env_path}")
        return

    print(f"\n Using account: {GMAIL_USER}")

    # Test read
    read_ok = test_gmail_read()

    # Test send (test mode only)
    send_ok = test_gmail_send(test_mode=True)

    # Summary
    print("\n" + "="*50)
    print("  SUMMARY")
    print("="*50)
    print(f"\n  Read emails (IMAP):  {'PASS' if read_ok else 'FAIL'}")
    print(f"  Send emails (SMTP):  {'PASS' if send_ok else 'FAIL'}")

    if read_ok and send_ok:
        print("\n Gmail is fully connected!")
        print("\n Your AI Employee can now:")
        print("   - Read your inbox")
        print("   - Draft email responses")
        print("   - Send emails (with approval)")

    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
