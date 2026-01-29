# AI Employee Watchers

Automated monitoring scripts that detect new items and create action files for Claude Code to process.

## Overview

The Watcher system is the "sensory layer" of your AI Employee. Each watcher monitors a specific source (Gmail, LinkedIn, files) and creates markdown files in the `/Needs_Action` folder when something requires attention.

## Current Watchers

### ✅ Gmail Watcher
**Status:** Implemented
**Monitors:** Gmail inbox for unread emails
**Priority Detection:** Keywords like "urgent", "invoice", "deadline"
**Output:** Creates `/Needs_Action/Emails/EMAIL_*.md` files

### 🔄 LinkedIn Watcher (Coming Soon)
**Status:** Planned
**Monitors:** LinkedIn messages and connection requests
**Output:** Creates `/Needs_Action/LinkedIn/LINKEDIN_*.md` files

### 🔄 File System Watcher (Coming Soon)
**Status:** Planned
**Monitors:** Designated drop folder for files
**Output:** Creates `/Needs_Action/Projects/FILE_*.md` files

## Setup Instructions

### 1. Install Dependencies

```bash
cd watchers
uv sync
```

### 2. Configure Environment

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env
```

### 3. Set Up Gmail API

#### A. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable Gmail API

#### B. Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Application type: "Desktop app"
4. Download credentials JSON
5. Save as `credentials.json` in watchers/ directory

### 4. Test Gmail Watcher

```bash
# Run single test check
uv run gmail_watcher.py --test
```

### 5. Run Watcher Continuously

```bash
# Run in foreground
uv run gmail_watcher.py
```

## Next Steps

- [ ] Set up Gmail watcher
- [ ] Test with real emails
- [ ] Configure Claude Code integration