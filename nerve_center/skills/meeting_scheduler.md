# Skill: Meeting Scheduler

## Description
Handle meeting requests, check availability, and coordinate scheduling.

## Trigger
- Email with meeting/schedule keywords
- Calendar invite received
- Manual: "schedule meeting with X"

## Inputs
- `request`: Meeting request details
- `participants`: List of attendees
- `duration`: Meeting length (default: 30 min)
- `preferences`: Time preferences from Company_Handbook.md

## Process

### Step 1: Parse Request
```
Extract:
- Who is requesting
- Purpose/agenda of meeting
- Preferred times (if specified)
- Duration needed
- Meeting type (call, video, in-person)
```

### Step 2: Check Preferences
```
From Company_Handbook.md:
- Preferred meeting days (e.g., Tue-Thu)
- Preferred hours (e.g., 10 AM - 4 PM)
- Buffer time between meetings (e.g., 15 min)
- Max meetings per day (e.g., 4)
- Blackout times
```

### Step 3: Check Calendar
```
Via Calendar MCP:
- Get next 2 weeks availability
- Apply preferences filter
- Account for existing meetings
- Consider timezone differences
```

### Step 4: Generate Options
```
Provide 3-5 time slots:
- Sorted by preference alignment
- Spread across different days
- Include timezone conversion if needed
```

### Step 5: Draft Response

**If Can Auto-Schedule (existing contact, clear request):**
```
Hi [Name],

Thank you for wanting to connect! I'd be happy to schedule a call.

Here are some available times that work well:
- [Option 1] - [Day, Date at Time Timezone]
- [Option 2] - [Day, Date at Time Timezone]
- [Option 3] - [Day, Date at Time Timezone]

Alternatively, you can book directly: [Calendly link if available]

Please let me know what works best for you!

Best,
[Owner Name]
```

**If Needs Clarification:**
```
Hi [Name],

Thank you for reaching out! I'd be happy to find a time to connect.

To make sure I schedule this appropriately, could you let me know:
- What you'd like to discuss?
- Your preferred meeting length?
- Any time constraints I should know about?

Looking forward to it!

Best,
[Owner Name]
```

### Step 6: Handle Response
```
When slot is confirmed:
1. Create calendar event
2. Send confirmation
3. Set reminder (1 day before, 1 hour before)
4. Update Dashboard
```

## Validation Rules
- Never double-book
- Respect minimum 15-min buffer
- VIP contacts get priority slots
- New/unknown contacts: Require owner approval first
- External parties: Add extra 5-min buffer

## Output
```json
{
  "meeting_id": "mtg_123",
  "status": "draft_sent",
  "requester": "john@example.com",
  "proposed_slots": [
    "2026-01-28T14:00:00Z",
    "2026-01-29T10:00:00Z",
    "2026-01-30T15:00:00Z"
  ],
  "draft_location": "nerve_center/drafts/meeting_123.md",
  "requires_approval": false
}
```

## Meeting Types Support
- **Video Call**: Zoom, Google Meet, Teams links
- **Phone Call**: Include dial-in number
- **In-Person**: Include address, parking info
- **Hybrid**: Provide both options

## Timezone Handling
- Store all times in UTC internally
- Convert for display based on participant timezone
- Always include timezone in communications
- Handle DST transitions
