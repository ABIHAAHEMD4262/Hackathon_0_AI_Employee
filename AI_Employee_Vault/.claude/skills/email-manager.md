# Email Manager Skill

## Description
Manages email inbox monitoring, drafting replies, and sending approved emails.

## Triggers
- New email detected in Needs_Action/Emails/
- Approval granted for email reply
- User requests email summary

## Capabilities
1. **Monitor Inbox**: Check for new emails via Gmail IMAP
2. **Draft Replies**: Generate professional email responses
3. **Send Emails**: Send approved replies via SMTP
4. **Prioritize**: Classify emails by urgency (high/medium/low)

## Commands

### Check for new emails
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
source venv/bin/activate
python watchers/gmail_watcher_simple.py --test
```

### Send approved email
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
source venv/bin/activate
python watchers/email_sender.py "<to_email>" "<subject>" "<message>"
```

### Run approval executor
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
source venv/bin/activate
python watchers/approval_executor.py --test
```

## File Locations
- Incoming emails: `Needs_Action/Emails/`
- Draft replies: `Approvals/`
- Approved: `Approved/`
- Rejected: `Rejected/`

## Priority Keywords
urgent, asap, important, deadline, invoice, payment, contract, proposal, meeting, call, project, client

## Rules
1. Always create draft in Approvals/ folder for human review
2. Never auto-send emails without approval
3. Flag emails with "urgent" or "asap" as high priority
4. Log all email actions to Logs/ folder
