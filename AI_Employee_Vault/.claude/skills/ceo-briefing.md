# CEO Briefing Skill

## Description
Generates weekly executive briefings with business insights, task summaries, and recommendations.

## Triggers
- Every Monday at 7:00 AM (scheduled)
- User requests briefing
- End of week summary request

## Capabilities
1. **Task Analysis**: Summarize completed and pending tasks
2. **Communication Summary**: Digest of important emails/messages
3. **Bottleneck Detection**: Identify delayed tasks
4. **Recommendations**: Proactive suggestions for improvement

## Commands

### Generate CEO Briefing
```bash
cd /mnt/g/Hackathon_0/AI_Employee/AI_Employee_Vault
source venv/bin/activate
python watchers/ceo_briefing.py --generate
```

### Generate for specific date range
```bash
python watchers/ceo_briefing.py --start 2026-01-15 --end 2026-01-21
```

## File Locations
- Generated briefings: `Business/Briefings/`
- Task data: `Tasks/` and `Done/`
- Email summaries: `Needs_Action/Emails/`

## Briefing Sections
1. **Executive Summary** - High-level overview
2. **Tasks Completed** - What was accomplished
3. **Tasks Pending** - What needs attention
4. **Bottlenecks** - Delayed items
5. **Communications** - Important messages received
6. **Recommendations** - AI suggestions

## Output Format
```markdown
# Monday Morning CEO Briefing
## Week of [DATE]

### Executive Summary
[2-3 sentence overview]

### Completed Tasks
- [x] Task 1
- [x] Task 2

### Pending/Blocked
- [ ] Task 3 (blocked by: reason)

### Key Communications
- Email from [sender] about [topic]
- WhatsApp from [contact] regarding [subject]

### Recommendations
1. [Actionable suggestion]
2. [Optimization opportunity]
```

## Rules
1. Generate every Monday automatically
2. Include only actionable insights
3. Flag overdue items prominently
4. Keep briefing under 2 pages
5. Use bullet points for readability
