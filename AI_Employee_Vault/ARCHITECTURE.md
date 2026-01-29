# AI Employee Architecture Documentation

**Version:** 1.0
**Author:** Syeda Abiha Ahmed
**Last Updated:** January 2026

---

## Overview

The AI Employee is an autonomous business management system that:
- Monitors communications (Gmail, LinkedIn, Social Media)
- Drafts responses using AI
- Requires human approval for sensitive actions
- Executes approved actions automatically
- Maintains comprehensive audit trails

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI EMPLOYEE SYSTEM                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐              │
│  │   WATCHERS  │   │   BRAIN     │   │   HANDS     │              │
│  │  (Sensors)  │   │ (Claude)    │   │   (MCP)     │              │
│  ├─────────────┤   ├─────────────┤   ├─────────────┤              │
│  │ Gmail       │──▶│ Orchestrator│──▶│ Email Server│              │
│  │ LinkedIn    │   │ Ralph Loop  │   │ Social Media│              │
│  │ File System │   │ CEO Briefing│   │ (Future)    │              │
│  └─────────────┘   └─────────────┘   └─────────────┘              │
│         │                │                   │                     │
│         ▼                ▼                   ▼                     │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │                    OBSIDIAN VAULT                             ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         ││
│  │  │  Inbox   │ │  Needs   │ │ Pending  │ │   Done   │         ││
│  │  │          │▶│  Action  │▶│ Approval │▶│          │         ││
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘         ││
│  │                     │              │                          ││
│  │                     ▼              ▼                          ││
│  │  ┌──────────────────────────────────────────────────────┐    ││
│  │  │  Dashboard.md  │  Company_Handbook.md  │  Plans/     │    ││
│  │  └──────────────────────────────────────────────────────┘    ││
│  └───────────────────────────────────────────────────────────────┘│
│                              │                                     │
│                              ▼                                     │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │                      HUMAN                                    ││
│  │              (Reviews & Approves in Obsidian)                 ││
│  └───────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Watchers (Perception Layer)

**Purpose:** Monitor external sources and create action files.

| Watcher | File | What It Monitors |
|---------|------|------------------|
| Gmail | `gmail_watcher.py` | New emails, priority detection |
| LinkedIn | `linkedin_watcher.py` | Messages, notifications, posts queue |
| Base | `base_watcher.py` | Abstract base class for all watchers |

**Flow:**
```
External Event → Watcher Detects → Creates .md file → /Needs_Action/
```

### 2. Brain (Reasoning Layer)

**Purpose:** Process tasks, make decisions, create plans.

| Component | File | Function |
|-----------|------|----------|
| Orchestrator | `orchestrator.py` | Coordinates all components, creates Plan.md |
| Ralph Wiggum | `ralph_wiggum_loop.py` | Persistent execution with retry |
| CEO Briefing | `ceo_briefing.py` | Weekly business summaries |
| Approval Workflow | `approval_workflow.py` | Human-in-the-loop approvals |

**Ralph Wiggum Loop:**
```python
while task_not_complete:
    try:
        execute_step()
        if needs_approval:
            wait_for_human()
    except:
        retry_with_backoff()
```

### 3. Hands (Action Layer - MCP Servers)

**Purpose:** Execute approved actions.

| MCP Server | File | Actions |
|------------|------|---------|
| Email | `email_server.py` | Send emails, draft emails |
| Social Media | `social_media_server.py` | Post to FB, IG, Twitter |

**MCP Tool Pattern:**
```python
{
    "name": "send_email",
    "parameters": {
        "to": "recipient@email.com",
        "subject": "Subject",
        "body": "Content"
    }
}
```

### 4. Memory (Obsidian Vault)

**Purpose:** Persistent storage and human interface.

```
AI_Employee_Vault/
├── Dashboard.md              # Status overview
├── Company_Handbook.md       # Business rules & policies
├── Inbox/                    # Raw incoming items
├── Needs_Action/             # Items requiring processing
│   ├── Emails/
│   ├── LinkedIn/
│   └── Projects/
├── In_Progress/              # Currently being worked on
├── Pending_Approval/         # Awaiting human OK
├── Approved/                 # Human approved, ready to execute
├── Done/                     # Completed tasks
├── Rejected/                 # Human rejected
├── Failed/                   # Failed tasks (for retry)
├── Quarantine/               # Problematic items isolated
├── Plans/                    # Execution plans
├── Clients/                  # Client information
├── Business/                 # Business documents
│   └── CEO_Briefings/
├── Marketing/                # Marketing content
│   ├── LinkedIn_Queue/
│   ├── LinkedIn_Posted/
│   └── Social_Queue/
├── Skills/                   # Agent skill definitions
├── Logs/                     # Audit trails
│   ├── Audit/
│   ├── Daily/
│   ├── Errors/
│   └── System/
├── watchers/                 # Python monitoring scripts
├── mcp_servers/              # Action servers
└── scripts/                  # Startup & utility scripts
```

---

## Data Flow

### Email Processing Flow

```
1. New email arrives
   │
2. Gmail Watcher detects (every 2 min)
   │
3. Creates: /Needs_Action/Emails/EMAIL_001.md
   │
4. Orchestrator picks up task
   │
5. Creates: /Plans/PLAN_EMAIL_001.json
   │
6. Ralph Wiggum executes steps:
   │
   ├─▶ Step 1: Analyze email content
   │
   ├─▶ Step 2: Draft response
   │        │
   │        ▼
   │   Creates: /Pending_Approval/EMAIL_DRAFT_001.md
   │
   ├─▶ Step 3: Wait for human approval
   │        │
   │        ▼
   │   Human checks [x] APPROVE in Obsidian
   │
   ├─▶ Step 4: Send email via MCP
   │        │
   │        ▼
   │   Email Server sends via Gmail SMTP
   │
   └─▶ Step 5: Archive
            │
            ▼
      Moves to: /Done/EMAIL_001.md
```

---

## Approval Workflow

### Status Markers
Human approves by checking checkboxes in markdown:
- `[x] **APPROVE**` → Execute action
- `[x] **REJECT**` → Don't execute, move to /Rejected
- `[x] **EDIT**` → Modify content, keep in /Pending_Approval

### Approval Detection
```python
if '[x]' in content and 'approve' in content.lower():
    return APPROVED
elif '[x]' in content and 'reject' in content.lower():
    return REJECTED
```

---

## Error Handling

### Recovery Strategies

| Strategy | When Used | Action |
|----------|-----------|--------|
| RETRY | Temporary failures | Exponential backoff retry |
| FALLBACK | Primary method fails | Use simpler alternative |
| SKIP | Non-critical failure | Continue with next task |
| ALERT | Needs human help | Create alert in /Needs_Action |
| QUARANTINE | Problematic item | Isolate for manual review |

### Circuit Breaker
- After 5 consecutive errors → Stop trying that operation
- Auto-reset after 15 minutes
- Prevents cascading failures

---

## Agent Skills

Skills define what the AI Employee can do:

### email_management
- Read emails
- Draft responses
- Send approved emails

### linkedin_management
- Monitor notifications
- Create post drafts
- Manage content queue

### task_management
- Process task queue
- Create execution plans
- Update dashboard

---

## Security Considerations

### Human-in-the-Loop
- ALL external actions require approval
- No auto-send for emails
- No auto-post to social media

### Credentials
- Stored in .env (never committed)
- App passwords for Gmail (not main password)
- OAuth tokens for social media

### Audit Trail
- Every action logged
- Checksums for log integrity
- Daily and error logs separate

---

## Tier Summary

| Tier | Status | Key Features |
|------|--------|--------------|
| Bronze | ✅ Complete | Vault, Dashboard, Gmail Watcher |
| Silver | ✅ Complete | LinkedIn, MCP, Approvals, Orchestrator |
| Gold | ✅ Complete | Social Media, CEO Briefing, Ralph Loop, Audit |
| Platinum | 🔄 In Progress | Cloud deployment, 24/7 operation |

---

## Running the System

### Start All Services
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/scripts
./run_ai_employee.sh start
```

### Check Status
```bash
./run_ai_employee.sh status
```

### Generate CEO Briefing
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault/watchers
python3 ceo_briefing.py /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
```

---

## Future Enhancements

1. **Real-time Dashboard** - Next.js web UI
2. **Mobile Notifications** - Push alerts for approvals
3. **Voice Interface** - Voice commands for approvals
4. **Multi-agent** - Specialized agents for different domains
5. **Learning** - AI learns from your approval patterns

---

## Lessons Learned

1. **Human control is essential** - Never auto-execute sensitive actions
2. **Markdown is powerful** - Simple, version-controlled, readable
3. **Persistence matters** - Ralph Wiggum pattern prevents lazy agents
4. **Logging everything** - You'll thank yourself when debugging
5. **Start simple** - Bronze tier first, then build up

---

*Documentation for AI Employee Hackathon*
*Syeda Abiha Ahmed - Full-Stack AI/ML Engineer*
