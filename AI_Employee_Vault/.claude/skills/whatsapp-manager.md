# WhatsApp Manager Skill

## Description
Monitors WhatsApp Web for important messages and manages responses.

## Triggers
- New WhatsApp message with priority keywords
- Approval granted for WhatsApp reply
- User requests WhatsApp summary

## Capabilities
1. **Monitor Messages**: Watch WhatsApp Web for new messages
2. **Detect Priority**: Identify urgent messages by keywords
3. **Draft Replies**: Generate appropriate responses
4. **Create Action Items**: Convert messages to actionable tasks

## Commands

### Start WhatsApp Watcher (requires browser)
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
source venv/bin/activate
pip install playwright
playwright install chromium
python watchers/whatsapp_watcher.py --test
```

### Run continuously
```bash
python watchers/whatsapp_watcher.py
```

## File Locations
- Incoming messages: `Needs_Action/WhatsApp/`
- Draft replies: `Approvals/`
- Session data: `.whatsapp_session/`

## Priority Keywords
urgent, asap, important, deadline, help, invoice, payment, contract, proposal, meeting, call, project, client, order, emergency, critical, immediately, confirm

## Rules
1. First run requires QR code scan for login
2. Keep browser session for persistent login
3. Only process messages with priority keywords
4. Create action files for human review
5. Never auto-reply without approval
