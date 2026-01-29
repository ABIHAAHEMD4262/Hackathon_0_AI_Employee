# Task Orchestrator Skill

## Description
Coordinates all AI Employee tasks, manages the approval workflow, and ensures task completion.

## Triggers
- New item in Needs_Action/
- Approval granted in Approved/
- Scheduled task time reached
- Ralph Wiggum loop iteration

## Capabilities
1. **Task Routing**: Direct items to appropriate handlers
2. **Approval Management**: Process approved/rejected items
3. **Queue Management**: Handle execution queue
4. **Error Recovery**: Retry failed tasks with backoff
5. **Audit Logging**: Track all actions

## Commands

### Run Orchestrator (single pass)
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
source venv/bin/activate
python watchers/orchestrator.py --once
```

### Run continuously
```bash
python watchers/orchestrator.py
```

### Process approval queue
```bash
python watchers/approval_executor.py --test
```

### Run Ralph Wiggum loop
```bash
python watchers/ralph_wiggum_loop.py --task "Process all items in Needs_Action"
```

## File Locations
- Incoming: `Needs_Action/`
- Pending approval: `Approvals/`
- Approved: `Approved/`
- Rejected: `Rejected/`
- Completed: `Done/`
- Execution queue: `.queue/`
- Logs: `Logs/`

## Workflow
```
Needs_Action/ → Claude analyzes → Approvals/
                                      ↓
                              Human approves
                                      ↓
                              Approved/ → Executor → Done/
```

## Error Recovery Strategies
1. **RETRY**: Transient errors (network timeout)
2. **FALLBACK**: Use alternative method
3. **SKIP**: Non-critical failures
4. **ALERT**: Notify human
5. **QUARANTINE**: Isolate problematic items

## Rules
1. Never execute sensitive actions without approval
2. Log all actions with timestamps
3. Retry transient errors up to 3 times
4. Quarantine items that fail repeatedly
5. Alert human for critical errors
