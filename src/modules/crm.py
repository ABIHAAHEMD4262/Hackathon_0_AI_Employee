"""
CRM Module
==========
Contact Relationship Management for tracking clients, leads, and interactions.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib


class ContactType(Enum):
    """Types of contacts."""
    CLIENT = "client"
    LEAD = "lead"
    PARTNER = "partner"
    VENDOR = "vendor"
    PERSONAL = "personal"
    OTHER = "other"


class ContactStatus(Enum):
    """Contact engagement status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CHURNED = "churned"
    PROSPECT = "prospect"


class LeadStage(Enum):
    """Sales pipeline stages."""
    NEW = "new"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class InteractionType(Enum):
    """Types of interactions."""
    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"
    MESSAGE = "message"
    NOTE = "note"
    TASK = "task"


@dataclass
class Interaction:
    """Represents an interaction with a contact."""
    id: str
    contact_id: str
    type: InteractionType
    timestamp: datetime
    summary: str
    details: str = ""
    channel: str = ""
    sentiment: str = "neutral"  # positive, neutral, negative
    follow_up_needed: bool = False
    follow_up_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "contact_id": self.contact_id,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "summary": self.summary,
            "details": self.details,
            "channel": self.channel,
            "sentiment": self.sentiment,
            "follow_up_needed": self.follow_up_needed,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Interaction':
        return cls(
            id=data["id"],
            contact_id=data["contact_id"],
            type=InteractionType(data["type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            summary=data["summary"],
            details=data.get("details", ""),
            channel=data.get("channel", ""),
            sentiment=data.get("sentiment", "neutral"),
            follow_up_needed=data.get("follow_up_needed", False),
            follow_up_date=datetime.fromisoformat(data["follow_up_date"]) if data.get("follow_up_date") else None,
            metadata=data.get("metadata", {})
        )


@dataclass
class Contact:
    """Represents a contact in the CRM."""
    id: str
    name: str
    email: str
    type: ContactType = ContactType.OTHER
    status: ContactStatus = ContactStatus.ACTIVE

    # Additional info
    company: str = ""
    title: str = ""
    phone: str = ""
    linkedin: str = ""
    twitter: str = ""
    website: str = ""
    address: str = ""
    timezone: str = ""

    # CRM fields
    lead_stage: Optional[LeadStage] = None
    lead_value: float = 0.0
    tags: List[str] = field(default_factory=list)
    notes: str = ""

    # Tracking
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_contact: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None

    # VIP flag
    is_vip: bool = False

    # Metadata
    source: str = ""  # How we got this contact
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "type": self.type.value,
            "status": self.status.value,
            "company": self.company,
            "title": self.title,
            "phone": self.phone,
            "linkedin": self.linkedin,
            "twitter": self.twitter,
            "website": self.website,
            "address": self.address,
            "timezone": self.timezone,
            "lead_stage": self.lead_stage.value if self.lead_stage else None,
            "lead_value": self.lead_value,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_contact": self.last_contact.isoformat() if self.last_contact else None,
            "next_follow_up": self.next_follow_up.isoformat() if self.next_follow_up else None,
            "is_vip": self.is_vip,
            "source": self.source,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Contact':
        return cls(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            type=ContactType(data.get("type", "other")),
            status=ContactStatus(data.get("status", "active")),
            company=data.get("company", ""),
            title=data.get("title", ""),
            phone=data.get("phone", ""),
            linkedin=data.get("linkedin", ""),
            twitter=data.get("twitter", ""),
            website=data.get("website", ""),
            address=data.get("address", ""),
            timezone=data.get("timezone", ""),
            lead_stage=LeadStage(data["lead_stage"]) if data.get("lead_stage") else None,
            lead_value=data.get("lead_value", 0.0),
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            last_contact=datetime.fromisoformat(data["last_contact"]) if data.get("last_contact") else None,
            next_follow_up=datetime.fromisoformat(data["next_follow_up"]) if data.get("next_follow_up") else None,
            is_vip=data.get("is_vip", False),
            source=data.get("source", ""),
            metadata=data.get("metadata", {})
        )


class CRMModule:
    """
    CRM module for managing contacts and relationships.

    Features:
    - Contact management (CRUD)
    - Interaction tracking
    - Lead pipeline management
    - Follow-up reminders
    - VIP identification
    - Contact enrichment
    """

    def __init__(self, data_path: str = "nerve_center/crm"):
        self.data_path = Path(data_path)
        self.contacts_file = self.data_path / "contacts.json"
        self.interactions_file = self.data_path / "interactions.json"

        self.contacts: Dict[str, Contact] = {}
        self.interactions: Dict[str, List[Interaction]] = {}  # contact_id -> interactions

        self.logger = logging.getLogger('CRM')

        # Ensure directories exist
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self._load_data()

    def _load_data(self):
        """Load contacts and interactions from disk."""
        try:
            if self.contacts_file.exists():
                with open(self.contacts_file, 'r') as f:
                    data = json.load(f)
                    for c in data:
                        contact = Contact.from_dict(c)
                        self.contacts[contact.id] = contact

            if self.interactions_file.exists():
                with open(self.interactions_file, 'r') as f:
                    data = json.load(f)
                    for contact_id, interactions in data.items():
                        self.interactions[contact_id] = [
                            Interaction.from_dict(i) for i in interactions
                        ]

            self.logger.info(f"Loaded {len(self.contacts)} contacts")

        except Exception as e:
            self.logger.error(f"Error loading CRM data: {e}")

    def _save_data(self):
        """Save contacts and interactions to disk."""
        try:
            with open(self.contacts_file, 'w') as f:
                json.dump([c.to_dict() for c in self.contacts.values()], f, indent=2)

            with open(self.interactions_file, 'w') as f:
                interactions_data = {
                    cid: [i.to_dict() for i in interactions]
                    for cid, interactions in self.interactions.items()
                }
                json.dump(interactions_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error saving CRM data: {e}")

    def _generate_id(self, prefix: str, unique_data: str) -> str:
        """Generate a unique ID."""
        hash_input = f"{prefix}-{unique_data}-{datetime.now().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]

    # Contact Management
    def add_contact(
        self,
        name: str,
        email: str,
        contact_type: ContactType = ContactType.OTHER,
        **kwargs
    ) -> Contact:
        """Add a new contact."""
        # Check for existing contact
        existing = self.find_contact_by_email(email)
        if existing:
            self.logger.info(f"Contact already exists: {email}")
            return existing

        contact_id = self._generate_id("contact", email)
        contact = Contact(
            id=contact_id,
            name=name,
            email=email,
            type=contact_type,
            **kwargs
        )

        self.contacts[contact_id] = contact
        self.interactions[contact_id] = []
        self._save_data()

        self.logger.info(f"Added contact: {name} ({email})")
        return contact

    def update_contact(self, contact_id: str, **updates) -> Optional[Contact]:
        """Update a contact's information."""
        if contact_id not in self.contacts:
            return None

        contact = self.contacts[contact_id]

        for key, value in updates.items():
            if hasattr(contact, key):
                if key == 'type' and isinstance(value, str):
                    value = ContactType(value)
                elif key == 'status' and isinstance(value, str):
                    value = ContactStatus(value)
                elif key == 'lead_stage' and isinstance(value, str):
                    value = LeadStage(value)
                setattr(contact, key, value)

        contact.updated_at = datetime.now()
        self._save_data()

        return contact

    def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact."""
        if contact_id not in self.contacts:
            return False

        del self.contacts[contact_id]
        self.interactions.pop(contact_id, None)
        self._save_data()

        return True

    def find_contact_by_email(self, email: str) -> Optional[Contact]:
        """Find a contact by email address."""
        email_lower = email.lower()
        for contact in self.contacts.values():
            if contact.email.lower() == email_lower:
                return contact
        return None

    def find_contacts(
        self,
        query: Optional[str] = None,
        contact_type: Optional[ContactType] = None,
        status: Optional[ContactStatus] = None,
        tags: Optional[List[str]] = None,
        is_vip: Optional[bool] = None
    ) -> List[Contact]:
        """Search contacts with filters."""
        results = []

        for contact in self.contacts.values():
            # Apply filters
            if query:
                query_lower = query.lower()
                if not any([
                    query_lower in contact.name.lower(),
                    query_lower in contact.email.lower(),
                    query_lower in contact.company.lower()
                ]):
                    continue

            if contact_type and contact.type != contact_type:
                continue

            if status and contact.status != status:
                continue

            if tags and not any(tag in contact.tags for tag in tags):
                continue

            if is_vip is not None and contact.is_vip != is_vip:
                continue

            results.append(contact)

        return results

    # Interaction Tracking
    def add_interaction(
        self,
        contact_id: str,
        interaction_type: InteractionType,
        summary: str,
        details: str = "",
        channel: str = "",
        **kwargs
    ) -> Optional[Interaction]:
        """Add an interaction with a contact."""
        if contact_id not in self.contacts:
            return None

        interaction_id = self._generate_id("interaction", contact_id)
        interaction = Interaction(
            id=interaction_id,
            contact_id=contact_id,
            type=interaction_type,
            timestamp=datetime.now(),
            summary=summary,
            details=details,
            channel=channel,
            **kwargs
        )

        if contact_id not in self.interactions:
            self.interactions[contact_id] = []

        self.interactions[contact_id].append(interaction)

        # Update last contact
        self.contacts[contact_id].last_contact = datetime.now()
        self.contacts[contact_id].updated_at = datetime.now()

        self._save_data()
        return interaction

    def get_interactions(
        self,
        contact_id: str,
        limit: int = 10,
        interaction_type: Optional[InteractionType] = None
    ) -> List[Interaction]:
        """Get interactions for a contact."""
        interactions = self.interactions.get(contact_id, [])

        if interaction_type:
            interactions = [i for i in interactions if i.type == interaction_type]

        # Sort by timestamp descending
        interactions.sort(key=lambda x: x.timestamp, reverse=True)

        return interactions[:limit]

    # Follow-up Management
    def get_follow_ups(self, days_ahead: int = 7) -> List[Dict]:
        """Get contacts needing follow-up."""
        cutoff = datetime.now() + timedelta(days=days_ahead)
        follow_ups = []

        for contact in self.contacts.values():
            if contact.next_follow_up and contact.next_follow_up <= cutoff:
                follow_ups.append({
                    'contact': contact,
                    'due_date': contact.next_follow_up,
                    'overdue': contact.next_follow_up < datetime.now()
                })

        # Sort by due date
        follow_ups.sort(key=lambda x: x['due_date'])
        return follow_ups

    def get_inactive_contacts(self, days: int = 30) -> List[Contact]:
        """Get contacts with no recent interaction."""
        cutoff = datetime.now() - timedelta(days=days)
        inactive = []

        for contact in self.contacts.values():
            if contact.status == ContactStatus.ACTIVE:
                if not contact.last_contact or contact.last_contact < cutoff:
                    inactive.append(contact)

        return inactive

    # Lead Management
    def get_pipeline(self) -> Dict[str, List[Contact]]:
        """Get leads organized by pipeline stage."""
        pipeline = {stage.value: [] for stage in LeadStage}

        for contact in self.contacts.values():
            if contact.lead_stage:
                pipeline[contact.lead_stage.value].append(contact)

        return pipeline

    def get_pipeline_value(self) -> Dict[str, float]:
        """Get total value by pipeline stage."""
        values = {stage.value: 0.0 for stage in LeadStage}

        for contact in self.contacts.values():
            if contact.lead_stage:
                values[contact.lead_stage.value] += contact.lead_value

        return values

    def advance_lead(self, contact_id: str) -> Optional[Contact]:
        """Advance a lead to the next pipeline stage."""
        if contact_id not in self.contacts:
            return None

        contact = self.contacts[contact_id]
        if not contact.lead_stage:
            contact.lead_stage = LeadStage.NEW
        else:
            stages = list(LeadStage)
            current_idx = stages.index(contact.lead_stage)
            if current_idx < len(stages) - 1:
                contact.lead_stage = stages[current_idx + 1]

        contact.updated_at = datetime.now()
        self._save_data()
        return contact

    # Analytics
    def get_stats(self) -> Dict[str, Any]:
        """Get CRM statistics."""
        return {
            "total_contacts": len(self.contacts),
            "by_type": {
                ct.value: len([c for c in self.contacts.values() if c.type == ct])
                for ct in ContactType
            },
            "by_status": {
                cs.value: len([c for c in self.contacts.values() if c.status == cs])
                for cs in ContactStatus
            },
            "vip_count": len([c for c in self.contacts.values() if c.is_vip]),
            "pipeline_value": self.get_pipeline_value(),
            "follow_ups_due": len(self.get_follow_ups(days_ahead=7)),
            "inactive_30d": len(self.get_inactive_contacts(30))
        }

    def get_recent_interactions(self, limit: int = 20) -> List[Interaction]:
        """Get most recent interactions across all contacts."""
        all_interactions = []
        for interactions in self.interactions.values():
            all_interactions.extend(interactions)

        all_interactions.sort(key=lambda x: x.timestamp, reverse=True)
        return all_interactions[:limit]
