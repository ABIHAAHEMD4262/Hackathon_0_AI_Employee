# AI Employee - Claude Code Configuration

## Project Overview

This is an **AI Employee** system - an autonomous agent that manages personal and business tasks. It uses Claude Code as the reasoning engine, with watchers for perception and MCP servers for actions.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR                             │
│                   (orchestrator.py)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   WATCHERS   │───▶│    QUEUE     │───▶│ CLAUDE CODE  │  │
│  │  (Perception)│    │   (Events)   │    │ (Reasoning)  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                    │         │
│                                                    ▼         │
│                                          ┌──────────────┐   │
│                                          │ MCP SERVERS  │   │
│                                          │  (Actions)   │   │
│                                          └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
AI_Employee/
├── CLAUDE.md                    # This file - Claude Code configuration
├── src/
│   ├── orchestrator.py          # Main orchestration engine
│   ├── watchers/                # Watcher implementations
│   ├── actions/                 # MCP action handlers
│   ├── reasoning/               # Claude reasoning templates
│   └── utils/                   # Utility functions
├── nerve_center/                # The "brain" - Obsidian vault
│   ├── Dashboard.md             # Real-time status dashboard
│   ├── Company_Handbook.md      # Business rules and preferences
│   ├── Business_Goals.md        # Goals and objectives
│   ├── inbox/                   # Incoming events/files
│   ├── processed/               # Processed events archive
│   ├── templates/               # Response templates
│   ├── logs/                    # System logs
│   └── skills/                  # Agent skill definitions
├── config/                      # Configuration files
│   ├── mcp_config.json          # MCP server configuration
│   └── credentials/             # API credentials (gitignored)
├── tests/                       # Test files
├── docs/                        # Documentation
└── scripts/                     # Utility scripts
```

## Key Files to Reference

When processing tasks, always reference these files for context:

1. **`nerve_center/Company_Handbook.md`** - Contains:
   - Owner preferences and communication style
   - VIP contact list and handling rules
   - Financial approval thresholds
   - Automation boundaries (what AI can/cannot do)

2. **`nerve_center/Business_Goals.md`** - Contains:
   - Current priorities and objectives
   - Weekly/monthly targets
   - How to prioritize conflicting tasks

3. **`nerve_center/Dashboard.md`** - Update this with:
   - Task completions
   - Financial transactions
   - Important communications
   - System status

## Human-in-the-Loop (HITL) Rules

**CRITICAL**: Always follow these approval requirements:

### Auto-Approve (No human needed):
- Reading emails and categorizing
- Updating Dashboard
- Creating draft responses
- Organizing files
- Logging activities

### Requires Approval:
- Sending any email
- Any financial transaction > $0
- Scheduling meetings with external parties
- Sharing any business information
- Modifying Company Handbook

### Never Do Automatically:
- Delete files without backup
- Access banking systems
- Share credentials or sensitive data
- Make legal commitments
- Contact emergency services (except true emergencies)

## Event Processing Guidelines

When processing events from the inbox:

### Email Events
```
1. Read sender and subject
2. Check if sender is VIP (Company_Handbook.md)
3. Categorize: urgent/financial/meeting/general
4. If response needed:
   - Draft using Company Handbook style guide
   - Save draft for approval (unless auto-send enabled)
5. Update Dashboard
6. Move to processed/
```

### Invoice Events
```
1. Extract: vendor, amount, due date, invoice number
2. If amount > $100: Create approval request
3. Log to financial tracking
4. Update Dashboard
5. If recurring, add to expected expenses
```

### File Events
```
1. Determine file type and purpose
2. If invoice: process as invoice event
3. If document: summarize and categorize
4. Move to appropriate folder or processed/
5. Update Dashboard
```

## MCP Server Integration

Available MCP servers (configure in config/mcp_config.json):

| Server | Purpose | Usage |
|--------|---------|-------|
| filesystem | File operations | Reading/writing files in nerve_center |
| gmail | Email operations | Requires oauth setup |
| calendar | Google Calendar | Scheduling, availability |
| obsidian | Obsidian operations | Note management |

## Response Templates

Use templates from `nerve_center/templates/` when available:

- `email_response.md` - Standard email replies
- `meeting_request.md` - Scheduling responses
- `invoice_confirmation.md` - Invoice acknowledgments
- `out_of_office.md` - Absence responses

## Error Handling

When errors occur:
1. Log to `nerve_center/logs/errors.log`
2. Add to Dashboard error section
3. If critical, create high-priority event
4. Never crash silently - always notify

## Security Reminders

- Never log or display full API keys or passwords
- Use environment variables for sensitive data
- Check file permissions before operations
- Validate external input
- Don't execute arbitrary code from emails/files

## Commands

Available when running Claude Code in this project:

```bash
# Start the orchestrator
python src/orchestrator.py

# Check status
python src/orchestrator.py --status

# Run tests
python src/orchestrator.py --test

# View logs
tail -f nerve_center/logs/orchestrator.log
```

## Development Notes

- Python 3.10+ required
- Virtual environment recommended
- Run `pip install -r requirements.txt` for dependencies
- Test watchers individually before full integration
