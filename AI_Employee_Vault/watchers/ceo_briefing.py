"""
CEO Briefing Generator - Gold Tier Component
==============================================
Generates weekly "Monday Morning CEO Briefing" that summarizes:
1. Business performance
2. Tasks completed vs pending
3. Client communications
4. Financial overview (if connected)
5. Social media performance
6. Recommendations for the week

This transforms the AI from a chatbot into a proactive business partner.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CEOBriefing')


class CEOBriefingGenerator:
    """
    Generates comprehensive weekly business briefings.
    Think of it as your AI sending you a Monday morning report.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.briefings_folder = self.vault_path / 'Business' / 'CEO_Briefings'
        self.briefings_folder.mkdir(parents=True, exist_ok=True)

        # Key folders to analyze
        self.folders = {
            'needs_action': self.vault_path / 'Needs_Action',
            'in_progress': self.vault_path / 'In_Progress',
            'pending_approval': self.vault_path / 'Pending_Approval',
            'done': self.vault_path / 'Done',
            'clients': self.vault_path / 'Clients',
            'plans': self.vault_path / 'Plans',
            'logs': self.vault_path / 'Logs'
        }

        logger.info(f"CEO Briefing Generator initialized for: {vault_path}")

    def generate_weekly_briefing(self) -> Path:
        """
        Generate the full weekly CEO briefing.
        Returns path to the generated briefing file.
        """
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        briefing_filename = f'CEO_Briefing_{today.strftime("%Y%m%d")}.md'
        briefing_path = self.briefings_folder / briefing_filename

        # Collect all metrics
        task_metrics = self._analyze_tasks()
        communication_metrics = self._analyze_communications()
        social_metrics = self._analyze_social_media()
        system_health = self._check_system_health()
        recommendations = self._generate_recommendations(task_metrics, communication_metrics)

        # Generate the briefing
        briefing_content = f'''# 📊 Weekly CEO Briefing

**Generated:** {today.strftime('%A, %B %d, %Y at %I:%M %p')}
**Report Period:** {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}
**Business:** Syeda Abiha Ahmed - Full-Stack AI/ML Engineer

---

## 🎯 Executive Summary

Good morning! Here's your weekly business overview.

### Key Highlights
{self._generate_highlights(task_metrics, communication_metrics)}

---

## 📈 Task Performance

### This Week's Numbers

| Metric | Count | Status |
|--------|-------|--------|
| Tasks Completed | {task_metrics['completed']} | {'🟢 Good' if task_metrics['completed'] > 0 else '🔴 None'} |
| Tasks In Progress | {task_metrics['in_progress']} | {'🟡 Active' if task_metrics['in_progress'] > 0 else '⚪ None'} |
| Pending Approval | {task_metrics['pending_approval']} | {'🟠 Review needed' if task_metrics['pending_approval'] > 0 else '✅ Clear'} |
| New Tasks | {task_metrics['needs_action']} | {'🔴 Action needed' if task_metrics['needs_action'] > 0 else '✅ Clear'} |

### Completion Rate
{self._calculate_completion_rate(task_metrics)}

### Task Breakdown by Type
{self._task_breakdown(task_metrics)}

---

## 📧 Communications Summary

### Email Activity
| Metric | Count |
|--------|-------|
| Emails Received | {communication_metrics.get('emails_received', 0)} |
| Emails Responded | {communication_metrics.get('emails_responded', 0)} |
| Pending Response | {communication_metrics.get('emails_pending', 0)} |

### Response Time
- Average response time: {communication_metrics.get('avg_response_time', 'N/A')}
- Urgent emails handled: {communication_metrics.get('urgent_handled', 0)}

---

## 👥 Client Status

{self._client_summary()}

---

## 📱 Social Media Performance

| Platform | Posts | Engagement |
|----------|-------|------------|
| LinkedIn | {social_metrics.get('linkedin_posts', 0)} | {social_metrics.get('linkedin_engagement', 'N/A')} |
| Twitter | {social_metrics.get('twitter_posts', 0)} | {social_metrics.get('twitter_engagement', 'N/A')} |
| Facebook | {social_metrics.get('facebook_posts', 0)} | {social_metrics.get('facebook_engagement', 'N/A')} |

---

## 🔧 System Health

| Component | Status |
|-----------|--------|
| Gmail Watcher | {system_health.get('gmail_watcher', '❓ Unknown')} |
| LinkedIn Watcher | {system_health.get('linkedin_watcher', '❓ Unknown')} |
| Approval Workflow | {system_health.get('approval_workflow', '❓ Unknown')} |
| Orchestrator | {system_health.get('orchestrator', '❓ Unknown')} |
| Email Server | {system_health.get('email_server', '❓ Unknown')} |

### Recent Errors
{system_health.get('recent_errors', 'No errors detected this week.')}

---

## 💡 Recommendations for This Week

{recommendations}

---

## 📅 Upcoming Deadlines

{self._get_upcoming_deadlines()}

---

## 🎯 Focus Areas for This Week

Based on the analysis above, here are your priorities:

{self._generate_priorities(task_metrics, communication_metrics)}

---

## 📝 Action Items

{self._generate_action_items(task_metrics, communication_metrics)}

---

## 💰 Financial Overview

*Note: Connect accounting system (Odoo) for detailed financial metrics*

### Estimated This Month
- Revenue Target: $2,000 - $5,000
- Estimated Hours Available: 160 hours
- Hourly Rate: $75 - $100

---

## 📊 Weekly Comparison

| Metric | Last Week | This Week | Change |
|--------|-----------|-----------|--------|
| Tasks Completed | - | {task_metrics['completed']} | - |
| Response Rate | - | {communication_metrics.get('response_rate', 'N/A')} | - |
| Posts Published | - | {social_metrics.get('total_posts', 0)} | - |

---

## 🗒️ Notes

- Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- Next briefing scheduled: {(today + timedelta(days=7)).strftime('%A, %B %d')}

---

*This briefing was generated automatically by your AI Employee.*
*Review in Obsidian and take action on the recommendations.*

**Have a productive week! 💪**
'''

        briefing_path.write_text(briefing_content)
        logger.info(f"Generated CEO briefing: {briefing_path}")

        # Also create a notification in Needs_Action
        self._create_briefing_notification(briefing_path)

        return briefing_path

    def _analyze_tasks(self) -> Dict[str, Any]:
        """Analyze tasks across all folders."""
        metrics = {
            'needs_action': 0,
            'in_progress': 0,
            'pending_approval': 0,
            'completed': 0,
            'by_type': {}
        }

        for folder_name, folder_path in self.folders.items():
            if not folder_path.exists():
                continue

            count = len(list(folder_path.rglob('*.md')))

            if folder_name == 'needs_action':
                metrics['needs_action'] = count
            elif folder_name == 'in_progress':
                metrics['in_progress'] = count
            elif folder_name == 'pending_approval':
                metrics['pending_approval'] = count
            elif folder_name == 'done':
                # Count only this week's completions
                week_ago = datetime.now() - timedelta(days=7)
                recent = [f for f in folder_path.glob('*.md')
                          if datetime.fromtimestamp(f.stat().st_mtime) > week_ago]
                metrics['completed'] = len(recent)

        return metrics

    def _analyze_communications(self) -> Dict[str, Any]:
        """Analyze communication activity."""
        metrics = {
            'emails_received': 0,
            'emails_responded': 0,
            'emails_pending': 0,
            'avg_response_time': 'N/A',
            'urgent_handled': 0,
            'response_rate': 'N/A'
        }

        # Check email logs
        email_logs = self.vault_path / 'Logs' / 'Email'
        if email_logs.exists():
            log_files = list(email_logs.glob('*.json'))
            for log_file in log_files:
                try:
                    with open(log_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            metrics['emails_responded'] += len(data)
                except:
                    pass

        # Check Needs_Action/Emails
        emails_folder = self.folders['needs_action'] / 'Emails'
        if emails_folder.exists():
            metrics['emails_pending'] = len(list(emails_folder.glob('*.md')))

        return metrics

    def _analyze_social_media(self) -> Dict[str, Any]:
        """Analyze social media activity."""
        metrics = {
            'linkedin_posts': 0,
            'twitter_posts': 0,
            'facebook_posts': 0,
            'total_posts': 0,
            'linkedin_engagement': 'N/A',
            'twitter_engagement': 'N/A',
            'facebook_engagement': 'N/A'
        }

        # Check posted content
        posted_folder = self.vault_path / 'Marketing' / 'Social_Posted'
        if posted_folder.exists():
            metrics['total_posts'] = len(list(posted_folder.glob('*.md')))

        linkedin_posted = self.vault_path / 'Marketing' / 'LinkedIn_Posted'
        if linkedin_posted.exists():
            metrics['linkedin_posts'] = len(list(linkedin_posted.glob('*.md')))

        return metrics

    def _check_system_health(self) -> Dict[str, Any]:
        """Check health of AI Employee components."""
        health = {
            'gmail_watcher': '✅ Built',
            'linkedin_watcher': '✅ Built',
            'approval_workflow': '✅ Built',
            'orchestrator': '✅ Built',
            'email_server': '✅ Built',
            'recent_errors': 'No errors detected.'
        }

        # Check for error logs
        error_logs = []
        logs_folder = self.vault_path / 'Logs'
        if logs_folder.exists():
            for log_file in logs_folder.rglob('*.log'):
                try:
                    content = log_file.read_text()
                    if 'ERROR' in content or 'error' in content:
                        error_logs.append(log_file.name)
                except:
                    pass

        if error_logs:
            health['recent_errors'] = f"Errors found in: {', '.join(error_logs[:5])}"

        return health

    def _generate_highlights(self, tasks: Dict, comms: Dict) -> str:
        """Generate executive summary highlights."""
        highlights = []

        if tasks['completed'] > 0:
            highlights.append(f"✅ **{tasks['completed']} tasks completed** this week")

        if tasks['pending_approval'] > 0:
            highlights.append(f"⚠️ **{tasks['pending_approval']} items awaiting your approval**")

        if tasks['needs_action'] > 0:
            highlights.append(f"📋 **{tasks['needs_action']} new tasks** need attention")

        if comms.get('emails_pending', 0) > 0:
            highlights.append(f"📧 **{comms['emails_pending']} emails** pending response")

        if not highlights:
            highlights.append("📊 Business is running smoothly. No urgent items.")

        return '\n'.join([f"- {h}" for h in highlights])

    def _calculate_completion_rate(self, tasks: Dict) -> str:
        """Calculate and format completion rate."""
        total = tasks['completed'] + tasks['in_progress'] + tasks['needs_action']
        if total == 0:
            return "No tasks tracked this week."

        rate = (tasks['completed'] / total) * 100
        bar_filled = int(rate / 10)
        bar_empty = 10 - bar_filled

        return f"{'█' * bar_filled}{'░' * bar_empty} {rate:.0f}% ({tasks['completed']}/{total} tasks)"

    def _task_breakdown(self, tasks: Dict) -> str:
        """Break down tasks by type."""
        # This would analyze file prefixes to categorize
        return """
| Type | Count |
|------|-------|
| Email Tasks | - |
| LinkedIn Tasks | - |
| Client Projects | - |
| Other | - |
"""

    def _client_summary(self) -> str:
        """Generate client status summary."""
        clients_folder = self.folders['clients']
        if not clients_folder.exists():
            return "No client folders found. Create folders in /Clients for each client."

        clients = [d.name for d in clients_folder.iterdir() if d.is_dir()]

        if not clients:
            return "No active clients. Focus on outreach this week!"

        summary = "| Client | Status | Last Contact |\n|--------|--------|-------------|\n"
        for client in clients[:5]:
            summary += f"| {client} | Active | - |\n"

        return summary

    def _get_upcoming_deadlines(self) -> str:
        """Get upcoming deadlines from plans and tasks."""
        # In production, this would parse frontmatter for due dates
        return """
| Deadline | Task | Priority |
|----------|------|----------|
| End of January | Hackathon Submission | High |
| Feb 21, 2026 | Business Launch | High |
| Ongoing | Portfolio Updates | Medium |
"""

    def _generate_priorities(self, tasks: Dict, comms: Dict) -> str:
        """Generate priority list for the week."""
        priorities = []

        if tasks['pending_approval'] > 0:
            priorities.append(f"1. **Review {tasks['pending_approval']} pending approvals** - AI drafted responses waiting for your OK")

        if tasks['needs_action'] > 0:
            priorities.append(f"2. **Process {tasks['needs_action']} new tasks** - Check Needs_Action folder")

        if comms.get('emails_pending', 0) > 0:
            priorities.append(f"3. **Respond to {comms['emails_pending']} pending emails** - Maintain response time")

        priorities.append("4. **Post on LinkedIn** - Keep building your network")
        priorities.append("5. **Review this briefing** - Note any issues")

        return '\n'.join(priorities)

    def _generate_action_items(self, tasks: Dict, comms: Dict) -> str:
        """Generate specific action items."""
        items = []
        items.append("- [ ] Review and approve/reject pending items in Obsidian")
        items.append("- [ ] Check Dashboard.md for urgent items")
        items.append("- [ ] Post 2-3 times on LinkedIn this week")
        items.append("- [ ] Update Company_Handbook if needed")
        items.append("- [ ] Review system logs for any issues")

        return '\n'.join(items)

    def _generate_recommendations(self, tasks: Dict, comms: Dict) -> str:
        """Generate AI recommendations based on analysis."""
        recs = []

        if tasks['pending_approval'] > 3:
            recs.append("⚠️ **High approval backlog** - Set aside 15 minutes to review pending items")

        if tasks['needs_action'] > 5:
            recs.append("📋 **Task queue growing** - Consider prioritizing or delegating")

        if comms.get('emails_pending', 0) > 3:
            recs.append("📧 **Email response needed** - Respond to pending emails to maintain reputation")

        recs.append("💡 **Growth tip**: Post your hackathon progress on LinkedIn to attract clients")
        recs.append("🎯 **Focus**: Quality over quantity - better to do fewer things well")

        return '\n'.join([f"{i+1}. {rec}" for i, rec in enumerate(recs)])

    def _create_briefing_notification(self, briefing_path: Path):
        """Create a notification in Needs_Action about the new briefing."""
        notif_path = self.folders['needs_action'] / f'BRIEFING_READY_{datetime.now().strftime("%Y%m%d")}.md'

        content = f'''---
type: notification
priority: high
created: {datetime.now().isoformat()}
status: pending
---

# 📊 Weekly CEO Briefing Ready

Your weekly business briefing has been generated.

**Location:** {briefing_path}

## Quick Actions
- [ ] Read the briefing
- [ ] Review pending approvals
- [ ] Note any action items

---

*Generated by AI Employee*
'''

        notif_path.write_text(content)


def generate_briefing(vault_path: str):
    """CLI function to generate a briefing."""
    generator = CEOBriefingGenerator(vault_path)
    briefing_path = generator.generate_weekly_briefing()
    print(f"✅ CEO Briefing generated: {briefing_path}")
    return briefing_path


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ceo_briefing.py <vault_path>")
        sys.exit(1)

    vault_path = sys.argv[1]
    generate_briefing(vault_path)
