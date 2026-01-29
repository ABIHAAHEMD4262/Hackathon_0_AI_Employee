# AI Employee - Comprehensive Documentation

> **Complete Technical Documentation & Testing Guide**

---

## Table of Contents

1. [Overview](#overview)
2. [Installation Guide](#installation-guide)
3. [Bronze Tier Features](#bronze-tier-features)
4. [Silver Tier Features](#silver-tier-features)
5. [Gold Tier Features](#gold-tier-features)
6. [Dashboard Guide](#dashboard-guide)
7. [Testing Guide](#testing-guide)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)

---

## Overview

### What is AI Employee?

AI Employee is an **autonomous agent system** that functions as your personal Digital Full-Time Equivalent (FTE). It operates on a simple principle:

```
PERCEIVE → REASON → ACT (with human approval)
```

### Core Components

| Component | Description | Location |
|-----------|-------------|----------|
| **Watchers** | Monitor inputs (email, social, files) | `watchers/` |
| **Orchestrator** | Coordinates tasks and creates plans | `watchers/orchestrator.py` |
| **MCP Servers** | Execute actions (send email, post) | `mcp_servers/` |
| **Dashboard** | Web UI for management | `dashboard/` |
| **Skills** | Agent capability definitions | `.claude/skills/` |

### Folder Structure

```
AI_Employee_Vault/
├── Needs_Action/          # Incoming tasks (watchers write here)
│   ├── Emails/            # Email notifications
│   ├── LinkedIn/          # LinkedIn notifications
│   ├── WhatsApp/          # WhatsApp messages
│   └── Alerts/            # System alerts
├── In_Progress/           # Tasks being processed
├── Pending_Approval/      # Needs human review
├── Approvals/             # Dashboard-created drafts
├── Approved/              # Human-approved items
├── Rejected/              # Human-rejected items
├── Done/                  # Completed tasks
├── Plans/                 # Execution plans (Plan.md files)
├── Logs/                  # Audit trails
│   ├── Email/
│   ├── SocialMedia/
│   ├── Errors/
│   ├── Scheduled/
│   └── RalphWiggum/
├── Business/              # Business documents
│   ├── CEO_Briefings/     # Weekly briefings
│   └── Goals/
├── Clients/               # Client folders
├── Marketing/             # Marketing content
│   ├── Social_Queue/      # Scheduled posts
│   └── Social_Posted/     # Published posts
├── Quarantine/            # Problematic items
├── Templates/             # Response templates
└── Assets/                # Images, files
```

---

## Installation Guide

### Prerequisites

```bash
# Required software
- Python 3.10+
- Node.js 18+
- Git
- Obsidian (optional, for vault viewing)
```

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd AI_Employee
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install Dashboard Dependencies

```bash
cd AI_Employee_Vault/dashboard
npm install
cd ../..
```

### Step 4: Configure Credentials

```bash
# Copy example env file
cp config/credentials/.env.example config/credentials/.env

# Edit with your credentials
nano config/credentials/.env
```

Required credentials:
```bash
# Gmail (use App Password, not regular password)
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# Optional: Social Media
LINKEDIN_ACCESS_TOKEN=xxx
TWITTER_API_KEY=xxx
FACEBOOK_ACCESS_TOKEN=xxx
```

### Step 5: Open in Obsidian

1. Open Obsidian
2. Click "Open folder as vault"
3. Select `AI_Employee_Vault` folder
4. The vault should now display with all folders

---

## Bronze Tier Features

### 1. Obsidian Vault Structure

**Location:** `AI_Employee_Vault/`

**Test:**
```bash
# Verify vault structure
ls -la AI_Employee_Vault/

# Should see: Dashboard.md, Company_Handbook.md, and all folders
```

### 2. Dashboard.md

**Location:** `AI_Employee_Vault/Dashboard.md`

**Purpose:** Real-time status display of your AI Employee

**Content includes:**
- System status (online/offline indicators)
- Task counts (pending, in progress, completed)
- Recent activity log
- Quick action links

**Test:** Open in Obsidian and verify all sections render correctly.

### 3. Company_Handbook.md

**Location:** `AI_Employee_Vault/Company_Handbook.md`

**Purpose:** Rules and preferences for the AI Employee
I  
**Sections:**
- Business Profile
- Communication Style Guide
- VIP Contacts
- Financial Approval Thresholds
- Automation Boundaries (what AI can/cannot do)

**Test:** Review and customize for your needs.

### 4. Gmail Watcher

**Location:** `watchers/gmail_watcher.py`

**Purpose:** Monitor Gmail inbox for new emails

**Test:**
```bash
cd AI_Employee_Vault
python watchers/gmail_watcher_simple.py --test
```

**Expected output:**
- Connection status
- Email count
- Sample emails (if any)

### 5. File System Watcher

**Location:** `src/watchers/filesystem_watcher.py`

**Purpose:** Monitor local folders for new files

**Test:**
```bash
# Create a test file in Inbox
echo "Test file content" > AI_Employee_Vault/Inbox/test_file.txt

# Check if watcher creates notification
ls AI_Employee_Vault/Needs_Action/
```

### 6. Agent Skills

**Location:** `.claude/skills/`

**Available Skills:**
| Skill File | Purpose |
|------------|---------|
| `email-manager.md` | Email handling |
| `social-media-manager.md` | Social media posting |
| `ceo-briefing.md` | Weekly briefings |
| `task-orchestrator.md` | Task management |
| `accounting-manager.md` | Financial tracking |
| `whatsapp-manager.md` | WhatsApp handling |

**Test:**
```bash
# List all skills
ls -la AI_Employee_Vault/.claude/skills/

# Read a skill
cat AI_Employee_Vault/.claude/skills/email-manager.md
```

---

## Silver Tier Features

### 1. Multiple Watchers

**Available Watchers:**
| Watcher | File | Purpose |
|---------|------|---------|
| Gmail | `gmail_watcher.py` | Email monitoring |
| LinkedIn | `linkedin_watcher.py` | LinkedIn notifications |
| WhatsApp | `whatsapp_watcher.py` | WhatsApp messages |
| Calendar | `src/watchers/calendar_watcher.py` | Calendar events |
| Slack | `src/watchers/slack_watcher.py` | Slack messages |
| Twitter | `src/watchers/twitter_watcher.py` | Twitter mentions |

**Test all watchers:**
```bash
# Test Gmail watcher
python AI_Employee_Vault/watchers/gmail_watcher_simple.py --test

# Test LinkedIn watcher
python AI_Employee_Vault/watchers/linkedin_watcher.py AI_Employee_Vault --test

# Check for created notifications
ls -la AI_Employee_Vault/Needs_Action/
```

### 2. MCP Email Server

**Location:** `mcp_servers/email_server.py`

**Capabilities:**
- `send_email` - Send approved emails
- `draft_email` - Create drafts for approval
- `list_drafts` - List pending drafts
- `get_email_status` - Check send status

**Test:**
```bash
python AI_Employee_Vault/mcp_servers/email_server.py AI_Employee_Vault

# In the interactive prompt:
# > draft test@example.com "Test Subject"
# > list
# > quit
```

### 3. Orchestrator & Plan.md

**Location:** `watchers/orchestrator.py`

**Purpose:** Creates execution plans for tasks

**Test:**
```bash
# Create a demo task
python AI_Employee_Vault/watchers/orchestrator.py AI_Employee_Vault --demo

# Check the created plan
ls -la AI_Employee_Vault/Plans/
cat AI_Employee_Vault/Plans/PLAN_*.md
```

**Plan.md Structure:**
```markdown
---
task_file: EMAIL_001.md
task_type: email
created: 2026-01-29T10:00:00
status: in_progress
---

# Execution Plan

## Steps
### Step 1: Analyze Email
- **Status:** [ ] Pending
- **Action:** Read and understand content

### Step 2: Draft Response
- **Status:** [ ] Pending
- **Requires Approval:** Yes
...
```

### 4. Human-in-the-Loop Approval

**Workflow:**
1. AI creates draft in `/Pending_Approval/`
2. Human reviews in dashboard or Obsidian
3. Human moves to `/Approved/` or `/Rejected/`
4. AI executes approved actions

**Test via Dashboard:**
1. Start dashboard: `cd AI_Employee_Vault/dashboard && npm run dev`
2. Go to Email tab, compose an email
3. Click "Save Draft for Approval"
4. Check Approvals tab - should see the draft
5. Click Approve or Reject

**Test via File System:**
```bash
# Check pending approvals
ls AI_Employee_Vault/Pending_Approval/

# Approve an item (move to Approved)
mv AI_Employee_Vault/Pending_Approval/EMAIL_DRAFT_*.md AI_Employee_Vault/Approved/
```

### 5. Scheduled Tasks

**Location:** `watchers/scheduled_tasks.py`

**Available Tasks:**
| Task | Schedule | Description |
|------|----------|-------------|
| `ceo_briefing` | Monday 7 AM | Weekly briefing |
| `email_check` | Every 5 min | Check emails |
| `health_check` | Hourly | System health |
| `process_approvals` | Every 10 min | Process approved items |
| `daily_summary` | 6 PM daily | Daily summary |

**Test:**
```bash
# List all tasks
python AI_Employee_Vault/watchers/scheduled_tasks.py AI_Employee_Vault --list

# Run a specific task
python AI_Employee_Vault/watchers/scheduled_tasks.py AI_Employee_Vault --task health_check --force

# Start daemon mode
python AI_Employee_Vault/watchers/scheduled_tasks.py AI_Employee_Vault --daemon
```

---

## Gold Tier Features

### 1. Social Media MCP Server

**Location:** `mcp_servers/social_media_server.py`

**Supported Platforms:**
- Facebook (Graph API)
- Instagram (Graph API)
- Twitter/X (API v2)

**Capabilities:**
- `post_to_social` - Post to platform
- `draft_social_post` - Create draft for approval
- `get_social_analytics` - Get analytics
- `generate_weekly_summary` - Weekly social report

**Test:**
```bash
python AI_Employee_Vault/mcp_servers/social_media_server.py AI_Employee_Vault

# Check platform status - will show which are configured
```

### 2. CEO Briefing Generator

**Location:** `watchers/ceo_briefing.py`

**Purpose:** Generate weekly executive briefings

**Output includes:**
- Executive summary
- Task performance metrics
- Communication summary
- Social media performance
- System health
- Recommendations
- Upcoming deadlines

**Test:**
```bash
# Generate a briefing
python AI_Employee_Vault/watchers/ceo_briefing.py AI_Employee_Vault

# Check the output
ls AI_Employee_Vault/Business/CEO_Briefings/
cat AI_Employee_Vault/Business/CEO_Briefings/CEO_Briefing_*.md
```

### 3. Ralph Wiggum Loop

**Location:** `watchers/ralph_wiggum_loop.py`

**Purpose:** Persistent task execution - keeps trying until complete

**Features:**
- Automatic retry with exponential backoff
- Approval waiting
- Step-by-step execution
- Error recovery

**Test:**
```bash
# Start the Ralph Wiggum loop
python AI_Employee_Vault/watchers/ralph_wiggum_loop.py AI_Employee_Vault

# It will:
# 1. Scan /Needs_Action for tasks
# 2. Create execution plans
# 3. Execute step by step
# 4. Wait for approvals when needed
# 5. Move completed tasks to /Done
```

### 4. Error Recovery System

**Location:** `watchers/error_recovery.py`

**Recovery Strategies:**
| Strategy | Description |
|----------|-------------|
| `RETRY` | Exponential backoff retry |
| `FALLBACK` | Use simpler method |
| `SKIP` | Skip and continue |
| `ALERT` | Alert human |
| `QUARANTINE` | Isolate problematic item |

**Features:**
- Circuit breaker pattern (stops after 5 consecutive errors)
- Automatic alerts
- Quarantine system
- Detailed error logging

**Test:**
```bash
python AI_Employee_Vault/watchers/error_recovery.py AI_Employee_Vault

# Check created alerts
ls AI_Employee_Vault/Needs_Action/Alerts/
```

### 5. Audit Logging

**Log Locations:**
| Log Type | Location |
|----------|----------|
| Email logs | `Logs/Email/` |
| Social media logs | `Logs/SocialMedia/` |
| Error logs | `Logs/Errors/` |
| Scheduled task logs | `Logs/Scheduled/` |
| Ralph Wiggum logs | `Logs/RalphWiggum/` |

**Log Format (JSON):**
```json
{
  "timestamp": "2026-01-29T10:30:00Z",
  "action_type": "email_send",
  "actor": "claude_code",
  "target": "client@example.com",
  "parameters": {"subject": "Invoice #123"},
  "approval_status": "approved",
  "result": "success"
}
```

**Test:**
```bash
# Check logs
ls -la AI_Employee_Vault/Logs/

# View error logs
cat AI_Employee_Vault/Logs/Errors/errors_*.json
```

---

## Dashboard Guide

### Starting the Dashboard

```bash
cd AI_Employee_Vault/dashboard
npm run dev
# Open http://localhost:3000
```

### Dashboard Tabs

#### 1. Command Center
- Natural language task input
- Quick action buttons
- Activity log
- Active agent status

**Test:**
1. Type "Write a LinkedIn post about AI automation"
2. Click Send or press Enter
3. Should switch to Social Media tab with topic filled

#### 2. Email Composer
- Recipient selection (from CRM)
- Subject line
- Tone selector (Professional/Friendly/Formal)
- AI draft generation
- Save for approval

**Test:**
1. Enter email: test@example.com
2. Enter subject: "Meeting Request"
3. Select tone: Professional
4. Click "Generate AI Draft"
5. Review generated content
6. Click "Save Draft for Approval"
7. Check Approvals tab

#### 3. Social Media
- Platform selection (LinkedIn, Twitter, Facebook, Instagram)
- Topic input
- AI content generation
- Character count
- Save for approval

**Test:**
1. Select LinkedIn
2. Enter topic: "AI in Business"
3. Click "Generate LinkedIn Post"
4. Review content
5. Click "Save for Approval"

#### 4. CRM
- Contact list
- VIP indicators
- Contact types (Client/Lead)
- Stats overview

#### 5. Financial
- Invoice upload
- Expense tracking
- Financial stats (AR, AP, Pipeline)

**Test:**
1. Click upload area
2. Select a PDF file
3. Click "Process"
4. Check if added to records

#### 6. Tasks
- Task list with status
- Priority indicators
- Due dates
- Progress stats

#### 7. Approvals
- Pending approval items
- Approve/Reject buttons
- Item preview

**Test:**
1. Create an email draft
2. Go to Approvals tab
3. Click "Approve" or "Reject"
4. Check Approved/ or Rejected/ folder

#### 8. Settings
- Connection status for all services
- API configuration info
- Automation rules toggles

---

## Testing Guide

### Complete Test Suite

Run all tests:
```bash
# 1. Check system status
python run.py --status

# 2. Create demo tasks
python run.py --demo

# 3. Test email server
python AI_Employee_Vault/mcp_servers/email_server.py AI_Employee_Vault

# 4. Test social media server
python AI_Employee_Vault/mcp_servers/social_media_server.py AI_Employee_Vault

# 5. Test CEO briefing
python AI_Employee_Vault/watchers/ceo_briefing.py AI_Employee_Vault

# 6. Test orchestrator
python AI_Employee_Vault/watchers/orchestrator.py AI_Employee_Vault --demo

# 7. Test scheduled tasks
python AI_Employee_Vault/watchers/scheduled_tasks.py AI_Employee_Vault --task health_check --force

# 8. Test error recovery
python AI_Employee_Vault/watchers/error_recovery.py AI_Employee_Vault

# 9. Start dashboard
cd AI_Employee_Vault/dashboard && npm run dev
```

### Dashboard API Tests

```bash
# Test dashboard API
curl http://localhost:3000/api/dashboard

# Test drafts API
curl -X POST http://localhost:3000/api/drafts \
  -H "Content-Type: application/json" \
  -d '{"type":"email_draft","data":{"to":"test@example.com","subject":"Test","body":"Hello"}}'

# Test approve API
curl -X POST http://localhost:3000/api/approve \
  -H "Content-Type: application/json" \
  -d '{"id":"email_draft_123456","action":"approve"}'
```

---

## Troubleshooting

### Obsidian Not Opening Vault

**Problem:** Vault doesn't appear in Obsidian

**Solution:**
1. Ensure `.obsidian` folder exists in `AI_Employee_Vault`
2. Check folder permissions
3. Try: File → Open folder as vault → Select AI_Employee_Vault

### Dashboard Not Starting

**Problem:** `npm run dev` fails

**Solution:**
```bash
cd AI_Employee_Vault/dashboard
rm -rf node_modules
rm package-lock.json
npm install
npm run dev
```

### Gmail Authentication Failed

**Problem:** Gmail watcher can't connect

**Solution:**
1. Use App Password, not regular password
2. Generate at: https://myaccount.google.com/apppasswords
3. Enable 2FA first
4. Use 16-character password without spaces

### Approvals Not Working

**Problem:** Approve/Reject buttons don't work

**Solution:**
1. Check browser console for errors
2. Ensure API routes exist: `dashboard/src/app/api/approve/route.ts`
3. Check folder permissions for Approved/Rejected folders

---

## API Reference

### Dashboard API Endpoints

#### GET /api/dashboard
Returns dashboard data including stats, approvals, activities.

#### POST /api/drafts
Create a new draft for approval.
```json
{
  "type": "email_draft",
  "data": {
    "to": "email@example.com",
    "subject": "Subject",
    "body": "Content",
    "tone": "professional"
  }
}
```

#### POST /api/approve
Approve or reject an item.
```json
{
  "id": "email_draft_123456",
  "action": "approve"  // or "reject"
}
```

### MCP Server Tools

#### Email Server
- `send_email(to, subject, body, reply_to?)`
- `draft_email(to, subject, body, context?)`
- `list_drafts()`
- `get_email_status(email_id)`

#### Social Media Server
- `post_to_social(platform, content, media_urls?)`
- `draft_social_post(platforms, content, scheduled_time?)`
- `get_social_analytics(platform)`
- `generate_weekly_summary()`

---

## Conclusion

This documentation covers all features of the AI Employee system across all three tiers:

- **Bronze:** Basic vault, single watcher, agent skills
- **Silver:** Multiple watchers, MCP servers, scheduling, HITL
- **Gold:** Social media, CEO briefings, Ralph Wiggum, error recovery

For questions or issues, refer to the Troubleshooting section or create an issue in the repository.

---

*Documentation generated for AI Employee Hackathon - January 2026*
