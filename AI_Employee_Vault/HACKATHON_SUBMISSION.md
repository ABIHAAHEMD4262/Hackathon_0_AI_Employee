# AI Employee - Hackathon Submission

## Project Overview

**AI Employee** is an autonomous business assistant that handles routine tasks like email management, social media, and communications - with human-in-the-loop approval for important actions.

### The Problem
Business owners and professionals spend hours daily on repetitive tasks:
- Reading and responding to emails
- Managing social media posts
- Scheduling meetings
- Generating reports

### The Solution
AI Employee automates these tasks while keeping humans in control:
1. **Monitors** your inbox and social media
2. **Drafts** responses and content
3. **Waits** for your approval on the dashboard
4. **Executes** approved actions automatically

---

## Features Implemented

### Bronze Tier ✅
- Obsidian Vault structure for data storage
- Gmail Watcher - monitors inbox for new emails
- Basic dashboard (markdown)

### Silver Tier ✅
- LinkedIn Watcher - monitors for messages/connections
- MCP Server for email actions
- Human-in-the-loop approval system
- Orchestrator to coordinate components

### Gold Tier ✅
- Social Media MCP (Facebook, Instagram, Twitter)
- Weekly CEO Briefing generator
- Ralph Wiggum Loop (persistent task execution)
- Comprehensive audit logging
- Error recovery with circuit breaker pattern

### Platinum Tier ✅
- Docker containerization
- Cloud deployment ready (Oracle Cloud, Railway)
- 24/7 operation capability

### Dashboard UI ✅
- Real-time Next.js dashboard
- Stats overview (tasks pending, completed, etc.)
- One-click approve/reject for pending items
- System health monitoring
- Activity log

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Watchers | Python 3.12 |
| Email | Gmail IMAP/SMTP |
| Dashboard | Next.js 14, React, TypeScript |
| Styling | Tailwind CSS |
| Storage | Obsidian Vault (Markdown) |
| Deployment | Docker, Docker Compose |

---

## How It Works

```
┌─────────────────┐
│   Gmail Inbox   │
└────────┬────────┘
         │ IMAP
         ▼
┌─────────────────┐
│  Gmail Watcher  │ ─── Checks every 2 min
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Action Files   │ ─── Needs_Action/Emails/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Dashboard     │ ─── http://localhost:3001
│   (You Review)  │
└────────┬────────┘
         │ Approve/Reject
         ▼
┌─────────────────┐
│    Executor     │ ─── Processes approved items
└────────┬────────┘
         │ SMTP
         ▼
┌─────────────────┐
│   Email Sent    │
└─────────────────┘
```

---

## Quick Start

### 1. Setup Environment
```bash
cd AI_Employee_Vault
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install python-dotenv
```

### 2. Configure Credentials
```bash
# Edit .env file
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password
```

### 3. Start AI Employee
```bash
# Terminal 1: Start watchers
python start_ai_employee.py

# Terminal 2: Start dashboard
cd dashboard
npm install
npm run dev
```

### 4. Open Dashboard
Navigate to: http://localhost:3001

---

## Demo Flow

1. **Send a test email** to your Gmail from another account
2. **Wait 2 minutes** for Gmail Watcher to detect it
3. **Open dashboard** - see the email in pending approvals
4. **Click Approve** - email reply is sent automatically
5. **Check sender's inbox** - they received your reply!

---

## File Structure

```
AI_Employee_Vault/
├── .env                     # Credentials
├── start_ai_employee.py     # Master startup script
├── watchers/
│   ├── gmail_watcher_simple.py
│   ├── email_sender.py
│   ├── approval_executor.py
│   ├── linkedin_watcher.py
│   └── ceo_briefing.py
├── mcp_servers/
│   └── social_media_server.py
├── dashboard/
│   ├── src/app/
│   │   ├── page.tsx
│   │   └── api/
│   └── src/components/
├── Needs_Action/            # Incoming items
├── Approvals/               # Pending approval
├── Approved/                # Approved items
├── Rejected/                # Rejected items
├── Logs/                    # Daily logs
└── cloud/                   # Docker files
```

---

## What Makes This Special

1. **Human-in-the-Loop**: AI drafts, human approves - no fully autonomous actions
2. **Real Working System**: Actually sends emails, not just mockups
3. **Extensible**: Easy to add new watchers (Slack, WhatsApp, etc.)
4. **Hackable**: Uses Obsidian markdown - easy to inspect and modify
5. **Cloud Ready**: Docker setup for 24/7 operation

---

## Future Improvements

- [ ] AI-powered email drafting with GPT
- [ ] Calendar integration
- [ ] Slack/Discord watchers
- [ ] Voice commands
- [ ] Mobile app

---

## Created By

**Syeda Abiha Ahmed**
- Full-Stack AI/ML Engineer
- GitHub: [@AbihaCodes](https://github.com/AbihaCodes)
- Portfolio: [abiha.dev](https://abiha.dev)

---

*Built for Hackathon 2026*
