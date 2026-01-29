"""
Analytics Module
================
Analytics, insights, and reporting for the AI Employee system.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict


@dataclass
class MetricData:
    """A single metric data point."""
    name: str
    value: float
    timestamp: datetime
    category: str = ""
    tags: Dict[str, str] = field(default_factory=dict)


class AnalyticsModule:
    """
    Analytics and insights module.

    Features:
    - Productivity metrics
    - Communication analytics
    - Financial trends
    - Goal tracking
    - AI-generated insights
    - Custom reporting
    """

    def __init__(
        self,
        data_path: str = "nerve_center/analytics",
        crm_module=None,
        financial_module=None,
        project_module=None
    ):
        self.data_path = Path(data_path)
        self.metrics_file = self.data_path / "metrics.json"
        self.insights_file = self.data_path / "insights.json"

        # Module references
        self.crm = crm_module
        self.financial = financial_module
        self.projects = project_module

        # Data storage
        self.metrics: List[MetricData] = []
        self.insights: List[Dict] = []
        self.daily_stats: Dict[str, Dict] = {}

        self.logger = logging.getLogger('Analytics')

        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self._load_data()

    def _load_data(self):
        """Load analytics data from disk."""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    self.metrics = [
                        MetricData(
                            name=m["name"],
                            value=m["value"],
                            timestamp=datetime.fromisoformat(m["timestamp"]),
                            category=m.get("category", ""),
                            tags=m.get("tags", {})
                        )
                        for m in data
                    ]

            if self.insights_file.exists():
                with open(self.insights_file, 'r') as f:
                    self.insights = json.load(f)

        except Exception as e:
            self.logger.error(f"Error loading analytics data: {e}")

    def _save_data(self):
        """Save analytics data to disk."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump([
                    {
                        "name": m.name,
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "category": m.category,
                        "tags": m.tags
                    }
                    for m in self.metrics[-10000:]  # Keep last 10000 metrics
                ], f, indent=2)

            with open(self.insights_file, 'w') as f:
                json.dump(self.insights[-100:], f, indent=2)  # Keep last 100 insights

        except Exception as e:
            self.logger.error(f"Error saving analytics data: {e}")

    # Metric Tracking
    def track_metric(
        self,
        name: str,
        value: float,
        category: str = "",
        tags: Dict[str, str] = None
    ):
        """Track a metric data point."""
        metric = MetricData(
            name=name,
            value=value,
            timestamp=datetime.now(),
            category=category,
            tags=tags or {}
        )
        self.metrics.append(metric)
        self._save_data()

    def track_event(self, event_type: str, source: str, metadata: Dict = None):
        """Track an event occurrence."""
        self.track_metric(
            name=f"event_{event_type}",
            value=1,
            category="events",
            tags={"source": source, **(metadata or {})}
        )

    # Productivity Analytics
    def get_productivity_score(self, days: int = 7) -> Dict[str, Any]:
        """Calculate productivity score based on various factors."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Get data from modules
        tasks_completed = 0
        tasks_created = 0
        avg_response_time = 0
        emails_processed = 0

        if self.projects:
            all_tasks = list(self.projects.tasks.values())
            tasks_completed = len([
                t for t in all_tasks
                if t.completed_at and t.completed_at >= start_date
            ])
            tasks_created = len([
                t for t in all_tasks
                if t.created_at >= start_date
            ])

        # Calculate score components
        completion_rate = (tasks_completed / tasks_created * 100) if tasks_created > 0 else 0
        completion_score = min(100, completion_rate)

        # Get communication metrics
        comm_metrics = self._get_metric_sum("event_email_received", start_date, end_date)
        emails_processed = comm_metrics

        # Calculate overall score (weighted average)
        weights = {
            "task_completion": 0.4,
            "communication": 0.3,
            "consistency": 0.3
        }

        # Consistency score based on daily activity
        daily_activity = self._get_daily_activity(start_date, end_date)
        active_days = len([d for d in daily_activity.values() if d > 0])
        consistency_score = (active_days / days * 100)

        overall_score = (
            completion_score * weights["task_completion"] +
            min(100, emails_processed / 10 * 100) * weights["communication"] +
            consistency_score * weights["consistency"]
        )

        return {
            "overall_score": round(overall_score, 1),
            "period_days": days,
            "components": {
                "task_completion": {
                    "score": round(completion_score, 1),
                    "tasks_completed": tasks_completed,
                    "tasks_created": tasks_created
                },
                "communication": {
                    "emails_processed": emails_processed,
                    "score": round(min(100, emails_processed / 10 * 100), 1)
                },
                "consistency": {
                    "active_days": active_days,
                    "total_days": days,
                    "score": round(consistency_score, 1)
                }
            },
            "trend": self._calculate_trend("productivity", days)
        }

    def _get_metric_sum(self, name: str, start: datetime, end: datetime) -> float:
        """Sum metrics within a date range."""
        return sum(
            m.value for m in self.metrics
            if m.name == name and start <= m.timestamp <= end
        )

    def _get_daily_activity(self, start: datetime, end: datetime) -> Dict[str, int]:
        """Get activity counts by day."""
        daily = defaultdict(int)

        for m in self.metrics:
            if start <= m.timestamp <= end:
                day = m.timestamp.strftime("%Y-%m-%d")
                daily[day] += 1

        return dict(daily)

    def _calculate_trend(self, metric_type: str, days: int) -> str:
        """Calculate trend direction."""
        end_date = datetime.now()
        mid_date = end_date - timedelta(days=days // 2)
        start_date = end_date - timedelta(days=days)

        first_half = sum(
            m.value for m in self.metrics
            if m.category == metric_type and start_date <= m.timestamp < mid_date
        )
        second_half = sum(
            m.value for m in self.metrics
            if m.category == metric_type and mid_date <= m.timestamp <= end_date
        )

        if second_half > first_half * 1.1:
            return "up"
        elif second_half < first_half * 0.9:
            return "down"
        return "stable"

    # Communication Analytics
    def get_communication_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get communication statistics."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Aggregate by channel
        channels = ["email", "whatsapp", "slack", "discord", "sms", "linkedin", "twitter"]
        stats = {}

        for channel in channels:
            received = self._get_metric_sum(f"event_{channel}_received", start_date, end_date)
            sent = self._get_metric_sum(f"event_{channel}_sent", start_date, end_date)
            stats[channel] = {
                "received": int(received),
                "sent": int(sent),
                "total": int(received + sent)
            }

        total_received = sum(s["received"] for s in stats.values())
        total_sent = sum(s["sent"] for s in stats.values())

        return {
            "period_days": days,
            "total": {
                "received": total_received,
                "sent": total_sent,
                "total": total_received + total_sent
            },
            "by_channel": stats,
            "daily_average": {
                "received": round(total_received / days, 1),
                "sent": round(total_sent / days, 1)
            },
            "busiest_day": self._get_busiest_day(start_date, end_date),
            "trend": self._calculate_trend("communication", days)
        }

    def _get_busiest_day(self, start: datetime, end: datetime) -> Optional[str]:
        """Find the busiest day in a period."""
        daily = self._get_daily_activity(start, end)
        if not daily:
            return None
        return max(daily.items(), key=lambda x: x[1])[0]

    # Financial Analytics
    def get_financial_trends(self, months: int = 6) -> Dict[str, Any]:
        """Get financial trend data."""
        if not self.financial:
            return {"error": "Financial module not available"}

        end_date = datetime.now()
        trends = []

        for i in range(months):
            month_end = end_date - timedelta(days=30 * i)
            month_start = month_end - timedelta(days=30)

            summary = self.financial.get_summary(month_start, month_end)
            trends.append({
                "month": month_end.strftime("%Y-%m"),
                "revenue": summary.get("revenue", 0),
                "expenses": summary.get("expenses", 0),
                "net_profit": summary.get("net_profit", 0)
            })

        trends.reverse()

        # Calculate growth
        if len(trends) >= 2:
            latest = trends[-1]["revenue"]
            previous = trends[-2]["revenue"]
            revenue_growth = ((latest - previous) / previous * 100) if previous > 0 else 0
        else:
            revenue_growth = 0

        return {
            "period_months": months,
            "monthly_data": trends,
            "totals": {
                "revenue": sum(t["revenue"] for t in trends),
                "expenses": sum(t["expenses"] for t in trends),
                "net_profit": sum(t["net_profit"] for t in trends)
            },
            "averages": {
                "monthly_revenue": sum(t["revenue"] for t in trends) / months if months > 0 else 0,
                "monthly_expenses": sum(t["expenses"] for t in trends) / months if months > 0 else 0
            },
            "growth": {
                "revenue_mom": round(revenue_growth, 1)
            }
        }

    # Goal Tracking
    def get_goal_progress(self) -> Dict[str, Any]:
        """Get progress towards defined goals."""
        goals = []

        # Revenue goals (example)
        if self.financial:
            summary = self.financial.get_summary()
            goals.append({
                "name": "Monthly Revenue",
                "target": 10000,  # Would come from Business_Goals.md
                "current": summary.get("revenue", 0),
                "progress": min(100, summary.get("revenue", 0) / 10000 * 100),
                "status": "on_track" if summary.get("revenue", 0) >= 5000 else "at_risk"
            })

        # Task completion goals
        if self.projects:
            dashboard = self.projects.get_dashboard_data()
            completed = dashboard["overview"]["completed_today"]
            goals.append({
                "name": "Daily Tasks",
                "target": 5,
                "current": completed,
                "progress": min(100, completed / 5 * 100),
                "status": "on_track" if completed >= 3 else "at_risk"
            })

        # Client goals
        if self.crm:
            stats = self.crm.get_stats()
            active_clients = stats["by_type"].get("client", 0)
            goals.append({
                "name": "Active Clients",
                "target": 10,
                "current": active_clients,
                "progress": min(100, active_clients / 10 * 100),
                "status": "on_track" if active_clients >= 7 else "at_risk"
            })

        return {
            "goals": goals,
            "overall_progress": sum(g["progress"] for g in goals) / len(goals) if goals else 0,
            "at_risk_count": len([g for g in goals if g["status"] == "at_risk"])
        }

    # AI Insights
    def generate_insights(self) -> List[Dict]:
        """Generate AI-powered insights based on data patterns."""
        insights = []
        now = datetime.now()

        # Analyze communication patterns
        comm_stats = self.get_communication_stats(7)
        if comm_stats["total"]["received"] > 50:
            insights.append({
                "type": "observation",
                "category": "communication",
                "title": "High Email Volume",
                "description": f"You received {comm_stats['total']['received']} messages this week. Consider setting up more auto-responses.",
                "priority": "medium",
                "generated_at": now.isoformat()
            })

        # Analyze productivity
        productivity = self.get_productivity_score(7)
        if productivity["overall_score"] < 60:
            insights.append({
                "type": "warning",
                "category": "productivity",
                "title": "Productivity Below Target",
                "description": f"Your productivity score is {productivity['overall_score']}%. Focus on completing pending tasks.",
                "priority": "high",
                "generated_at": now.isoformat()
            })
        elif productivity["overall_score"] > 85:
            insights.append({
                "type": "achievement",
                "category": "productivity",
                "title": "Excellent Productivity",
                "description": f"Great job! Your productivity score is {productivity['overall_score']}%.",
                "priority": "low",
                "generated_at": now.isoformat()
            })

        # Analyze overdue items
        if self.projects:
            overdue = self.projects.get_tasks(overdue_only=True)
            if len(overdue) > 3:
                insights.append({
                    "type": "warning",
                    "category": "tasks",
                    "title": "Multiple Overdue Tasks",
                    "description": f"You have {len(overdue)} overdue tasks. Prioritize or reschedule them.",
                    "priority": "high",
                    "generated_at": now.isoformat()
                })

        # Analyze follow-ups
        if self.crm:
            follow_ups = self.crm.get_follow_ups(days_ahead=7)
            overdue_follow_ups = [f for f in follow_ups if f["overdue"]]
            if len(overdue_follow_ups) > 0:
                insights.append({
                    "type": "reminder",
                    "category": "crm",
                    "title": "Overdue Follow-ups",
                    "description": f"You have {len(overdue_follow_ups)} overdue follow-ups. Don't let relationships go cold.",
                    "priority": "medium",
                    "generated_at": now.isoformat()
                })

        # Store insights
        self.insights.extend(insights)
        self._save_data()

        return insights

    def get_recent_insights(self, limit: int = 10) -> List[Dict]:
        """Get most recent insights."""
        return sorted(
            self.insights,
            key=lambda x: x.get("generated_at", ""),
            reverse=True
        )[:limit]

    # Reporting
    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate comprehensive weekly report."""
        return {
            "period": {
                "start": (datetime.now() - timedelta(days=7)).isoformat(),
                "end": datetime.now().isoformat()
            },
            "productivity": self.get_productivity_score(7),
            "communication": self.get_communication_stats(7),
            "financial": self.get_financial_trends(1) if self.financial else None,
            "goals": self.get_goal_progress(),
            "insights": self.generate_insights(),
            "generated_at": datetime.now().isoformat()
        }

    def generate_dashboard_data(self) -> Dict[str, Any]:
        """Generate data for the analytics dashboard."""
        return {
            "productivity_score": self.get_productivity_score(7)["overall_score"],
            "communication_today": self.get_communication_stats(1)["total"],
            "goals_at_risk": self.get_goal_progress()["at_risk_count"],
            "recent_insights": self.get_recent_insights(5),
            "trends": {
                "productivity": self._calculate_trend("productivity", 7),
                "communication": self._calculate_trend("communication", 7)
            }
        }
