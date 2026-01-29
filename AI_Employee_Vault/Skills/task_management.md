# Agent Skill: Task Management

## Skill ID
`task_management`

## Description
Manages tasks and workflows for the AI Employee. Creates plans, tracks progress, and updates the Dashboard.

## Capabilities

### 1. Process Tasks
- Scan /Needs_Action for new tasks
- Analyze task type and priority
- Create execution plans (Plan.md)
- Move tasks through workflow stages

### 2. Create Plans
- Break complex tasks into steps
- Identify approval requirements
- Set priorities and deadlines
- Track completion status

### 3. Update Dashboard
- Count items in each folder
- Update status metrics
- Log daily activity
- Flag urgent items

## Usage

### Invocation
```
"Use the task_management skill to [action]"
```

### Examples
```
"Use task_management to process new tasks in Needs_Action"
"Use task_management to create a plan for this client inquiry"
"Use task_management to update the dashboard"
```

## Task Workflow

```
┌──────────────┐
│   INBOX      │  Raw input arrives
└──────┬───────┘
       │
       v
┌──────────────┐
│ NEEDS_ACTION │  Analyzed and ready for processing
└──────┬───────┘
       │
       v
┌──────────────┐
│ IN_PROGRESS  │  Plan created, being worked on
└──────┬───────┘
       │
       v
┌──────────────┐
│PEND_APPROVAL │  Requires human OK (sensitive actions)
└──────┬───────┘
       │
       v
┌──────────────┐
│   APPROVED   │  Human approved, ready to execute
└──────┬───────┘
       │
       v
┌──────────────┐
│    DONE      │  Completed and archived
└──────────────┘
```

## Priority Levels

| Priority | Response Time | Keywords |
|----------|---------------|----------|
| URGENT | < 1 hour | urgent, asap, emergency |
| HIGH | < 4 hours | important, client, deadline |
| MEDIUM | < 24 hours | request, inquiry |
| LOW | < 48 hours | fyi, optional |

## Plan Template

```markdown
---
task_file: [original file]
task_type: [type]
created: [timestamp]
status: in_progress
---

# Execution Plan

## Original Task
[Summary]

## Steps

### Step 1: [Name]
- Status: [ ] Pending
- Action: [What to do]
- Requires Approval: Yes/No

### Step 2: [Name]
...

## Progress Log

| Time | Step | Status | Notes |
|------|------|--------|-------|
```

## Files Used

| File | Purpose |
|------|---------|
| `/watchers/orchestrator.py` | Main task processor |
| `/Plans/*.md` | Execution plans |
| `/Needs_Action/**/*.md` | Incoming tasks |
| `/In_Progress/*.md` | Active tasks |
| `/Done/*.md` | Completed tasks |
| `/Dashboard.md` | Status overview |

## Dashboard Metrics Updated

- Tasks in Needs_Action
- Tasks in Progress
- Pending Approvals
- Completed Today
- Urgent Items

---

*Agent Skill for AI Employee - Task Management*
