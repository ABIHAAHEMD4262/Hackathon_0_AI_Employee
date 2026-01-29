"""
Project Management Module
=========================
Project and task tracking with milestones, deadlines, and progress monitoring.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import hashlib


class ProjectStatus(Enum):
    """Project status."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Task status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Task:
    """Represents a task."""
    id: str
    title: str
    description: str = ""
    project_id: Optional[str] = None

    # Status and priority
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM

    # Assignment
    assignee: str = ""
    created_by: str = ""

    # Dates
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    started_at: Optional[datetime] = None

    # Time tracking
    estimated_hours: float = 0
    actual_hours: float = 0

    # Dependencies
    blocked_by: List[str] = field(default_factory=list)  # Task IDs
    blocks: List[str] = field(default_factory=list)  # Task IDs

    # Organization
    tags: List[str] = field(default_factory=list)
    milestone_id: Optional[str] = None

    # Source tracking
    source: str = ""  # email, manual, auto-detected
    source_id: str = ""  # Original event ID if auto-created

    # Notes
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_overdue(self) -> bool:
        if self.status == TaskStatus.COMPLETED:
            return False
        if not self.due_date:
            return False
        return datetime.now() > self.due_date

    @property
    def days_until_due(self) -> Optional[int]:
        if not self.due_date:
            return None
        return (self.due_date - datetime.now()).days

    @property
    def is_blocked(self) -> bool:
        return len(self.blocked_by) > 0 or self.status == TaskStatus.BLOCKED

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "assignee": self.assignee,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "blocked_by": self.blocked_by,
            "blocks": self.blocks,
            "tags": self.tags,
            "milestone_id": self.milestone_id,
            "source": self.source,
            "source_id": self.source_id,
            "notes": self.notes,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            project_id=data.get("project_id"),
            status=TaskStatus(data.get("status", "todo")),
            priority=TaskPriority(data.get("priority", 3)),
            assignee=data.get("assignee", ""),
            created_by=data.get("created_by", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            estimated_hours=data.get("estimated_hours", 0),
            actual_hours=data.get("actual_hours", 0),
            blocked_by=data.get("blocked_by", []),
            blocks=data.get("blocks", []),
            tags=data.get("tags", []),
            milestone_id=data.get("milestone_id"),
            source=data.get("source", ""),
            source_id=data.get("source_id", ""),
            notes=data.get("notes", ""),
            metadata=data.get("metadata", {})
        )


@dataclass
class Milestone:
    """Represents a project milestone."""
    id: str
    project_id: str
    title: str
    description: str = ""
    due_date: Optional[datetime] = None
    completed: bool = False
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed": self.completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Milestone':
        return cls(
            id=data["id"],
            project_id=data["project_id"],
            title=data["title"],
            description=data.get("description", ""),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            completed=data.get("completed", False),
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
        )


@dataclass
class Project:
    """Represents a project."""
    id: str
    name: str
    description: str = ""
    client: str = ""
    client_contact: str = ""

    # Status
    status: ProjectStatus = ProjectStatus.PLANNING

    # Dates
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    start_date: Optional[datetime] = None
    deadline: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Budget
    budget: float = 0
    budget_spent: float = 0
    hourly_rate: float = 0

    # Organization
    tags: List[str] = field(default_factory=list)
    color: str = "#3498db"  # For UI

    # Notes
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def budget_remaining(self) -> float:
        return self.budget - self.budget_spent

    @property
    def budget_percentage(self) -> float:
        return (self.budget_spent / self.budget * 100) if self.budget > 0 else 0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "client": self.client,
            "client_contact": self.client_contact,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "budget": self.budget,
            "budget_spent": self.budget_spent,
            "hourly_rate": self.hourly_rate,
            "tags": self.tags,
            "color": self.color,
            "notes": self.notes,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Project':
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            client=data.get("client", ""),
            client_contact=data.get("client_contact", ""),
            status=ProjectStatus(data.get("status", "planning")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            start_date=datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            budget=data.get("budget", 0),
            budget_spent=data.get("budget_spent", 0),
            hourly_rate=data.get("hourly_rate", 0),
            tags=data.get("tags", []),
            color=data.get("color", "#3498db"),
            notes=data.get("notes", ""),
            metadata=data.get("metadata", {})
        )


class ProjectModule:
    """
    Project and task management module.

    Features:
    - Project CRUD
    - Task management
    - Milestone tracking
    - Time tracking
    - Dependency management
    - Progress reporting
    """

    def __init__(self, data_path: str = "nerve_center/projects"):
        self.data_path = Path(data_path)
        self.projects_file = self.data_path / "projects.json"
        self.tasks_file = self.data_path / "tasks.json"
        self.milestones_file = self.data_path / "milestones.json"

        self.projects: Dict[str, Project] = {}
        self.tasks: Dict[str, Task] = {}
        self.milestones: Dict[str, Milestone] = {}

        self.logger = logging.getLogger('Projects')

        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self._load_data()

    def _load_data(self):
        """Load project data from disk."""
        try:
            if self.projects_file.exists():
                with open(self.projects_file, 'r') as f:
                    data = json.load(f)
                    for p in data:
                        project = Project.from_dict(p)
                        self.projects[project.id] = project

            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                    for t in data:
                        task = Task.from_dict(t)
                        self.tasks[task.id] = task

            if self.milestones_file.exists():
                with open(self.milestones_file, 'r') as f:
                    data = json.load(f)
                    for m in data:
                        milestone = Milestone.from_dict(m)
                        self.milestones[milestone.id] = milestone

            self.logger.info(f"Loaded {len(self.projects)} projects, {len(self.tasks)} tasks")

        except Exception as e:
            self.logger.error(f"Error loading project data: {e}")

    def _save_data(self):
        """Save project data to disk."""
        try:
            with open(self.projects_file, 'w') as f:
                json.dump([p.to_dict() for p in self.projects.values()], f, indent=2)

            with open(self.tasks_file, 'w') as f:
                json.dump([t.to_dict() for t in self.tasks.values()], f, indent=2)

            with open(self.milestones_file, 'w') as f:
                json.dump([m.to_dict() for m in self.milestones.values()], f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving project data: {e}")

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        hash_input = f"{prefix}-{datetime.now().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]

    # Project Management
    def create_project(self, name: str, **kwargs) -> Project:
        """Create a new project."""
        project_id = self._generate_id("project")
        project = Project(id=project_id, name=name, **kwargs)

        self.projects[project_id] = project
        self._save_data()

        self.logger.info(f"Created project: {name}")
        return project

    def update_project(self, project_id: str, **updates) -> Optional[Project]:
        """Update a project."""
        if project_id not in self.projects:
            return None

        project = self.projects[project_id]

        for key, value in updates.items():
            if hasattr(project, key):
                if key == 'status' and isinstance(value, str):
                    value = ProjectStatus(value)
                setattr(project, key, value)

        project.updated_at = datetime.now()
        self._save_data()

        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self.projects.get(project_id)

    def get_projects(
        self,
        status: Optional[ProjectStatus] = None,
        client: Optional[str] = None
    ) -> List[Project]:
        """Get projects with filters."""
        results = []

        for project in self.projects.values():
            if status and project.status != status:
                continue
            if client and project.client != client:
                continue
            results.append(project)

        return sorted(results, key=lambda x: x.created_at, reverse=True)

    def get_project_progress(self, project_id: str) -> Dict[str, Any]:
        """Get project progress summary."""
        project = self.projects.get(project_id)
        if not project:
            return {}

        project_tasks = self.get_tasks(project_id=project_id)
        total = len(project_tasks)
        completed = len([t for t in project_tasks if t.status == TaskStatus.COMPLETED])
        in_progress = len([t for t in project_tasks if t.status == TaskStatus.IN_PROGRESS])
        blocked = len([t for t in project_tasks if t.is_blocked])
        overdue = len([t for t in project_tasks if t.is_overdue])

        milestones = self.get_milestones(project_id)
        milestones_completed = len([m for m in milestones if m.completed])

        total_estimated = sum(t.estimated_hours for t in project_tasks)
        total_actual = sum(t.actual_hours for t in project_tasks)

        return {
            "project_id": project_id,
            "project_name": project.name,
            "status": project.status.value,
            "tasks": {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "blocked": blocked,
                "overdue": overdue,
                "completion_percentage": (completed / total * 100) if total > 0 else 0
            },
            "milestones": {
                "total": len(milestones),
                "completed": milestones_completed,
                "completion_percentage": (milestones_completed / len(milestones) * 100) if milestones else 0
            },
            "time": {
                "estimated_hours": total_estimated,
                "actual_hours": total_actual,
                "variance": total_actual - total_estimated
            },
            "budget": {
                "total": project.budget,
                "spent": project.budget_spent,
                "remaining": project.budget_remaining,
                "percentage": project.budget_percentage
            }
        }

    # Task Management
    def create_task(
        self,
        title: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Task:
        """Create a new task."""
        task_id = self._generate_id("task")
        task = Task(id=task_id, title=title, project_id=project_id, **kwargs)

        self.tasks[task_id] = task
        self._save_data()

        self.logger.info(f"Created task: {title}")
        return task

    def update_task(self, task_id: str, **updates) -> Optional[Task]:
        """Update a task."""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        old_status = task.status

        for key, value in updates.items():
            if hasattr(task, key):
                if key == 'status' and isinstance(value, str):
                    value = TaskStatus(value)
                elif key == 'priority' and isinstance(value, int):
                    value = TaskPriority(value)
                setattr(task, key, value)

        task.updated_at = datetime.now()

        # Track status changes
        if 'status' in updates:
            new_status = task.status
            if old_status != TaskStatus.IN_PROGRESS and new_status == TaskStatus.IN_PROGRESS:
                task.started_at = datetime.now()
            elif old_status != TaskStatus.COMPLETED and new_status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
                # Unblock dependent tasks
                for blocked_task_id in task.blocks:
                    if blocked_task_id in self.tasks:
                        blocked_task = self.tasks[blocked_task_id]
                        if task_id in blocked_task.blocked_by:
                            blocked_task.blocked_by.remove(task_id)

        self._save_data()
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id not in self.tasks:
            return False

        del self.tasks[task_id]
        self._save_data()
        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_tasks(
        self,
        project_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assignee: Optional[str] = None,
        overdue_only: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[Task]:
        """Get tasks with filters."""
        results = []

        for task in self.tasks.values():
            if project_id and task.project_id != project_id:
                continue
            if status and task.status != status:
                continue
            if priority and task.priority != priority:
                continue
            if assignee and task.assignee != assignee:
                continue
            if overdue_only and not task.is_overdue:
                continue
            if tags and not any(tag in task.tags for tag in tags):
                continue
            results.append(task)

        # Sort by priority then due date
        return sorted(results, key=lambda x: (x.priority.value, x.due_date or datetime.max))

    def add_dependency(self, task_id: str, depends_on_id: str) -> bool:
        """Add a dependency between tasks."""
        if task_id not in self.tasks or depends_on_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        dependent = self.tasks[depends_on_id]

        if depends_on_id not in task.blocked_by:
            task.blocked_by.append(depends_on_id)
        if task_id not in dependent.blocks:
            dependent.blocks.append(task_id)

        self._save_data()
        return True

    def log_time(self, task_id: str, hours: float, notes: str = "") -> Optional[Task]:
        """Log time spent on a task."""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        task.actual_hours += hours
        task.updated_at = datetime.now()

        if notes:
            task.notes += f"\n[{datetime.now().isoformat()}] Logged {hours}h: {notes}"

        self._save_data()
        return task

    # Milestone Management
    def create_milestone(
        self,
        project_id: str,
        title: str,
        **kwargs
    ) -> Milestone:
        """Create a milestone."""
        milestone_id = self._generate_id("milestone")
        milestone = Milestone(
            id=milestone_id,
            project_id=project_id,
            title=title,
            **kwargs
        )

        self.milestones[milestone_id] = milestone
        self._save_data()

        return milestone

    def complete_milestone(self, milestone_id: str) -> Optional[Milestone]:
        """Mark a milestone as complete."""
        if milestone_id not in self.milestones:
            return None

        milestone = self.milestones[milestone_id]
        milestone.completed = True
        milestone.completed_at = datetime.now()

        self._save_data()
        return milestone

    def get_milestones(self, project_id: str) -> List[Milestone]:
        """Get milestones for a project."""
        return [
            m for m in self.milestones.values()
            if m.project_id == project_id
        ]

    # Reporting
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for task dashboard."""
        now = datetime.now()
        today_end = now.replace(hour=23, minute=59, second=59)
        week_end = now + timedelta(days=7)

        all_tasks = list(self.tasks.values())
        active_tasks = [t for t in all_tasks if t.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]]

        return {
            "overview": {
                "total_tasks": len(all_tasks),
                "active_tasks": len(active_tasks),
                "completed_today": len([
                    t for t in all_tasks
                    if t.completed_at and t.completed_at.date() == now.date()
                ]),
                "overdue": len([t for t in active_tasks if t.is_overdue]),
                "blocked": len([t for t in active_tasks if t.is_blocked])
            },
            "due_today": [
                t.to_dict() for t in active_tasks
                if t.due_date and t.due_date <= today_end
            ],
            "due_this_week": [
                t.to_dict() for t in active_tasks
                if t.due_date and today_end < t.due_date <= week_end
            ],
            "in_progress": [
                t.to_dict() for t in active_tasks
                if t.status == TaskStatus.IN_PROGRESS
            ],
            "projects_summary": [
                self.get_project_progress(p.id)
                for p in self.projects.values()
                if p.status == ProjectStatus.ACTIVE
            ]
        }
