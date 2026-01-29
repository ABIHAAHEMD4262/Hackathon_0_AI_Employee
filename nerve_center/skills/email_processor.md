# Skill: Email Processor

## Description
Process incoming emails, categorize them, and draft appropriate responses.

## Trigger
- New email event in inbox
- Manual invocation: "process email"

## Inputs
- `email_data`: JSON containing from, subject, body, date
- `handbook`: Path to Company_Handbook.md

## Process

### Step 1: Load Context
```
Read Company_Handbook.md to get:
- VIP contact list
- Communication style preferences
- Email triage rules
```

### Step 2: Analyze Email
```
Extract:
- Sender name and email
- Subject line keywords
- Body content summary
- Attachments (if any)
- Sentiment (urgent, normal, casual)
```

### Step 3: Categorize
```
Categories:
- URGENT: Contains urgent keywords or from VIP with high priority
- FINANCIAL: Invoice, payment, bill, receipt
- MEETING: Schedule, calendar, call, meeting request
- SALES: Proposal, quote, inquiry, lead
- SUPPORT: Help, issue, problem, question
- MARKETING: Newsletter, promotion, unsubscribe
- PERSONAL: From known personal contacts
- SPAM: Known spam patterns, blacklisted senders
```

### Step 4: Determine Action
```
Based on category:
- URGENT → Draft response immediately, flag for review
- FINANCIAL → Extract amounts, add to financial tracking
- MEETING → Check calendar availability, draft response
- SALES → Create lead record, draft follow-up
- SUPPORT → Create ticket, draft acknowledgment
- MARKETING → Archive (unless VIP)
- PERSONAL → Draft warm response
- SPAM → Archive, no response
```

### Step 5: Draft Response
```
Use template from Company_Handbook.md:
- Match formality level
- Use correct signature
- Include any standard disclaimers
```

### Step 6: Update Dashboard
```
Add to Dashboard.md:
- Recent activity log
- Email stats
- Pending responses
```

## Output
```json
{
  "email_id": "...",
  "category": "MEETING",
  "priority": 2,
  "action_taken": "draft_response",
  "draft_location": "nerve_center/drafts/email_123.md",
  "requires_approval": true,
  "summary": "Meeting request from John Doe for next Tuesday"
}
```

## Error Handling
- If sender not recognized: Default to NORMAL priority
- If template missing: Use generic professional response
- If Calendar API fails: Ask user for availability manually
