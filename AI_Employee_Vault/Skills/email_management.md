# Agent Skill: Email Management

## Skill ID
`email_management`

## Description
Manages email communications for the freelance business. Can read emails, draft responses, and send approved messages.

## Capabilities

### 1. Read Emails
- Check Gmail for new messages
- Identify priority emails (keywords: urgent, project, client)
- Create action files in /Needs_Action/Emails

### 2. Draft Responses
- Analyze email content
- Reference Company_Handbook for tone and templates
- Create draft in /Pending_Approval
- Never send without human approval

### 3. Send Approved Emails
- Read approved drafts from /Approved
- Send via Gmail SMTP
- Log all sent emails
- Move to /Done

## Usage

### Invocation
```
"Use the email_management skill to [action]"
```

### Examples
```
"Use email_management to check for new client inquiries"
"Use email_management to draft a response to the latest email"
"Use email_management to send the approved proposal"
```

## Required Context
- Access to vault: /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
- Email credentials: EMAIL_USER, EMAIL_PASS in environment
- Gmail API credentials: token.json

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│ New Email   │ --> │ Create Task │ --> │ Draft Reply  │
│ (Gmail)     │     │ (Needs_Act) │     │ (Pend_Appr)  │
└─────────────┘     └─────────────┘     └──────────────┘
                                               │
                                               v
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│ Log & Done  │ <-- │ Send Email  │ <-- │ Human Approv │
│ (/Done)     │     │ (MCP)       │     │ (Obsidian)   │
└─────────────┘     └─────────────┘     └──────────────┘
```

## Rules (from Company_Handbook)

1. **Always be professional** - Use templates from handbook
2. **Never auto-send** - All emails require approval
3. **Respond within 4 hours** - For client emails
4. **Flag urgent messages** - Priority: high for keywords
5. **Log everything** - Full audit trail

## Files Used

| File | Purpose |
|------|---------|
| `/watchers/gmail_watcher.py` | Monitor Gmail |
| `/mcp_servers/email_server.py` | Send emails |
| `/Needs_Action/Emails/*.md` | New email tasks |
| `/Pending_Approval/EMAIL_*.md` | Draft responses |
| `/Logs/Email/*.json` | Sent email logs |

## Error Handling

- **Auth failed**: Check EMAIL_USER and EMAIL_PASS (use app password)
- **Rate limited**: Wait 60 seconds, retry
- **Network error**: Log error, retry in 5 minutes
- **Invalid recipient**: Flag for human review

---

*Agent Skill for AI Employee - Email Management*
