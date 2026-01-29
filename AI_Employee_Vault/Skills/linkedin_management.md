# Agent Skill: LinkedIn Management

## Skill ID
`linkedin_management`

## Description
Manages LinkedIn presence for lead generation. Monitors notifications, creates posts, and engages with connections.

## Capabilities

### 1. Monitor LinkedIn
- Check for new messages
- Track connection requests
- Monitor post engagement
- Identify job opportunities

### 2. Create Content
- Draft LinkedIn posts from templates
- Queue posts in /Marketing/LinkedIn_Queue
- Create approval requests
- Never post without human approval

### 3. Engage with Network
- Draft responses to messages
- Prepare connection acceptance messages
- Track engagement metrics

## Usage

### Invocation
```
"Use the linkedin_management skill to [action]"
```

### Examples
```
"Use linkedin_management to create a post about my latest project"
"Use linkedin_management to check for new messages"
"Use linkedin_management to draft a response to the recruiter"
```

## Post Templates

### Project Showcase
```
🚀 Excited to share my latest project: [PROJECT_NAME]!

[DESCRIPTION]

Tech Stack: [TECHNOLOGIES]

Key Features:
[FEATURES]

Check it out: [LINK]

#AI #Development #Tech
```

### Availability Post
```
👋 Open for new projects!

I specialize in:
✅ AI-Powered Applications
✅ Full-Stack Development
✅ E-Commerce Automation
✅ Cloud-Native Deployment

Let's connect! DM me or email: abihaahmed413@gmail.com

#Freelance #AIEngineer #OpenForWork
```

### Learning Journey
```
📚 Learning Update!

This week I've been diving deep into [TOPIC].

Key takeaways:
[TAKEAWAYS]

What are you learning this week?

#LearningInPublic #Developer
```

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│ Create Post │ --> │ Queue Post  │ --> │ Approval Req │
│ (Template)  │     │ (Mkt/Queue) │     │ (Pend_Appr)  │
└─────────────┘     └─────────────┘     └──────────────┘
                                               │
                                               v
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│ Archive     │ <-- │ Post to LI  │ <-- │ Human Approv │
│ (Mkt/Posted)│     │ (API/Manual)│     │ (Obsidian)   │
└─────────────┘     └─────────────┘     └──────────────┘
```

## Posting Schedule (from Company_Handbook)

- **Frequency**: 2-3 posts per week
- **Best times**: Tuesday-Thursday, 9 AM or 12 PM
- **Content mix**: 40% projects, 30% learning, 30% engagement

## Files Used

| File | Purpose |
|------|---------|
| `/watchers/linkedin_watcher.py` | Monitor LinkedIn |
| `/Marketing/LinkedIn_Queue/*.md` | Queued posts |
| `/Marketing/LinkedIn_Posted/*.md` | Posted archive |
| `/Needs_Action/LinkedIn/*.md` | LinkedIn tasks |

## Rules

1. **Never auto-post** - All posts require approval
2. **Stay professional** - Review tone before posting
3. **Add value** - Don't just self-promote
4. **Engage authentically** - Respond to comments
5. **Track metrics** - Log engagement for learning

---

*Agent Skill for AI Employee - LinkedIn Management*
