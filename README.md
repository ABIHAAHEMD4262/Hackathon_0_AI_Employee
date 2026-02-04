# AI Employee - Personal AI Employee Hackathon

> Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.

![Tier](https://img.shields.io/badge/Tier-Gold-gold)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Claude Code](https://img.shields.io/badge/Powered%20by-Claude%20Code-blue)

## Overview

AI Employee is an autonomous agent system that manages personal and business tasks 24/7. It uses **Claude Code** as the reasoning engine, **Obsidian** as the knowledge base, and a **Next.js dashboard** for real-time management.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AI EMPLOYEE SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   WATCHERS   │───▶│    QUEUE     │───▶│ CLAUDE CODE  │  │
│  │  (Perception)│    │   (Events)   │    │ (Reasoning)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                                        │         │
│         ▼                                        ▼         │
│  ┌──────────────┐                      ┌──────────────┐   │
│  │   OBSIDIAN   │                      │ MCP SERVERS  │   │
│  │    VAULT     │                      │  (Actions)   │   │
│  └──────────────┘                      └──────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │              NEXT.JS DASHBOARD                      │   │
│  │   Email │ Social │ CRM │ Finance │ Approvals       │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Bronze Tier (Foundation) ✅
- [x] Obsidian vault with Dashboard.md and Company_Handbook.md
- [x] Gmail Watcher - monitors inbox for important emails
- [x] Basic folder structure (/Inbox, /Needs_Action, /Done)
- [x] Claude Code Agent Skills

### Silver Tier (Functional Assistant) ✅
- [x] Multiple Watchers (Gmail, LinkedIn, WhatsApp, Calendar, Slack, Twitter)
- [x] LinkedIn auto-posting capability
- [x] Plan.md reasoning loop (Orchestrator)
- [x] Email MCP Server for sending emails
- [x] Human-in-the-Loop (HITL) approval workflow
- [x] Scheduled tasks (cron-like scheduling)

### Gold Tier (Autonomous Employee) ✅
- [x] Facebook, Instagram, Twitter integration
- [x] CEO Briefing generation (weekly summaries)
- [x] Error recovery with circuit breaker pattern
- [x] Ralph Wiggum loop for persistent task execution
- [x] Comprehensive audit logging
- [x] Full documentation

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Obsidian (optional, for vault viewing)
- Gmail API credentials (for email features)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/AI_Employee.git
cd AI_Employee
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up the dashboard**
```bash
cd AI_Employee_Vault/dashboard
npm install
```

4. **Configure environment**
```bash
# Copy and edit the environment file
cp AI_Employee_Vault/.env.example AI_Employee_Vault/.env
# Add your Gmail credentials
```

5. **Start the dashboard**
```bash
cd AI_Employee_Vault/dashboard
npm run dev
```

6. **Open in browser**
```
http://localhost:3000
```

## Project Structure

```
AI_Employee/
├── AI_Employee_Vault/          # Obsidian vault (the "brain")
│   ├── .obsidian/              # Obsidian configuration
│   ├── dashboard/              # Next.js web dashboard
│   │   ├── src/app/            # Dashboard pages & API
│   │   └── package.json
│   ├── watchers/               # Python watcher scripts
│   │   ├── gmail_watcher.py    # Gmail monitoring
│   │   ├── linkedin_watcher.py # LinkedIn monitoring
│   │   ├── ceo_briefing.py     # CEO briefing generator
│   │   └── ralph_wiggum_loop.py # Persistent execution
│   ├── mcp_servers/            # MCP action servers
│   ├── Needs_Action/           # Incoming tasks queue
│   ├── Approvals/              # Pending human approvals
│   ├── Done/                   # Completed tasks
│   ├── Dashboard.md            # System status
│   └── Company_Handbook.md     # Business rules
├── nerve_center/               # Data storage (JSON)
│   ├── crm/contacts.json       # Contact database
│   ├── finances/               # Financial records
│   └── projects/tasks.json     # Task database
├── src/                        # Core Python source
│   ├── orchestrator.py         # Main orchestrator
│   └── watchers/               # Watcher implementations
├── config/                     # Configuration files
├── scripts/                    # Utility scripts
├── run.py                      # Main entry point
├── requirements.txt            # Python dependencies
└── CLAUDE.md                   # Claude Code instructions
```

## Dashboard Features

### Command Center
- Natural language commands ("Write a LinkedIn post about AI")
- Quick action buttons
- Activity log

### Email Tab
- Inbox display with live emails from Gmail
- Email composer with AI-generated drafts
- Tone selection (professional, friendly, formal)

### Approvals Tab
- **Outgoing Drafts**: Review and send emails/posts
- **Incoming Emails**: Approve (auto-reply) or Reject (archive)
- Human-in-the-loop for all sensitive actions

### Social Media Tab
- Post to LinkedIn, Twitter, Facebook, Instagram
- AI-generated content
- Platform-specific formatting

### CRM Tab
- Contact management
- Lead tracking
- VIP designation

### Financial Tab
- Invoice tracking
- Expense management
- AR/AP overview

### Tasks Tab
- Task creation and management
- Priority levels
- Due date tracking

### Settings Tab
- Service connections
- Automation rules
- CEO Briefing trigger

## Human-in-the-Loop (HITL)

All sensitive actions require human approval:

| Action | Auto-Approve | Requires Approval |
|--------|--------------|-------------------|
| Read emails | ✅ | - |
| Draft emails | ✅ | - |
| Send emails | - | ✅ |
| Social posts | - | ✅ |
| Payments > $0 | - | ✅ |

## Watchers

| Watcher | Purpose | Interval |
|---------|---------|----------|
| Gmail | Monitor inbox | 2 min |
| LinkedIn | Track messages | 5 min |
| WhatsApp | Business messages | 30 sec |
| Calendar | Events sync | 5 min |
| Slack | Team messages | 1 min |

## CEO Briefing

Generates weekly executive summaries including:
- Revenue and financial metrics
- Task completion rates
- Overdue items
- Bottleneck identification
- Proactive recommendations

Generate manually via Dashboard → Settings → "Generate CEO Briefing Now"

## Configuration

### Gmail Setup
1. Create a Google Cloud project
2. Enable Gmail API
3. Create OAuth credentials
4. Download `credentials.json` to `config/credentials/`
5. Run `python scripts/setup_google.py` for authentication

### SMTP for Sending Emails
Add to `AI_Employee_Vault/.env`:
```env
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

## Running Components

```bash
# Start the dashboard
cd AI_Employee_Vault/dashboard && npm run dev

# Run Gmail watcher
python AI_Employee_Vault/watchers/gmail_watcher.py

# Run scheduled tasks
python AI_Employee_Vault/watchers/scheduled_tasks.py --daemon

# Generate CEO briefing
python AI_Employee_Vault/watchers/ceo_briefing.py

# Run tests
python test_all_features.py
```

## Security

- Credentials stored in `.env` files (gitignored)
- HITL approval for all external actions
- Audit logging of all operations
- No auto-execution of destructive commands

## Tech Stack

- **Reasoning**: Claude Code (Anthropic)
- **Knowledge Base**: Obsidian (Markdown)
- **Dashboard**: Next.js 14, React 18, TailwindCSS
- **Watchers**: Python 3.10+
- **Email**: Gmail API, Nodemailer
- **Storage**: Local JSON files

## Demo Video

[Link to demo video - 5-10 minutes showing key features]

## License

MIT License - See LICENSE file

## Acknowledgments

- Anthropic for Claude Code
- Panaversity Hackathon Team
- The Obsidian community

---

**Built with Claude Code for the Personal AI Employee Hackathon 2026**

*Your AI Employee works 24/7 so you don't have to.*
