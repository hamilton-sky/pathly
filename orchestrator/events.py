"""Event types and schema for the event-sourced orchestrator."""

from dataclasses import dataclass, asdict, field
from typing import Optional, Any
from datetime import datetime
import json


@dataclass
class Event:
    """Base event class. All events are immutable once created."""

    type: str  # COMMAND, STATE_TRANSITION, FEEDBACK_EVENT, SYSTEM_EVENT
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)

    def to_jsonl(self) -> str:
        """Serialize event to JSONL format (one JSON per line)."""
        return json.dumps(asdict(self))

    @staticmethod
    def from_jsonl(line: str) -> "Event":
        """Deserialize event from JSONL format."""
        data = json.loads(line.strip())
        return Event(
            type=data["type"],
            timestamp=data.get("timestamp"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CommandEvent(Event):
    """COMMAND: User initiates a workflow command."""

    type: str = "COMMAND"
    name: str = ""  # e.g., "/team-flow"
    feature: str = ""  # e.g., "auth-service"


@dataclass
class StateTransitionEvent(Event):
    """STATE_TRANSITION: FSM moves from one state to another."""

    type: str = "STATE_TRANSITION"
    from_state: str = ""
    to_state: str = ""


@dataclass
class FeedbackEvent(Event):
    """FEEDBACK_EVENT: Feedback or issue detected."""

    type: str = "FEEDBACK_EVENT"
    status: str = ""  # OPEN or RESOLVED
    file: str = ""  # File path where feedback originates
    message: str = ""  # Feedback message


@dataclass
class SystemEvent(Event):
    """SYSTEM_EVENT: Internal system events (retry, error, etc)."""

    type: str = "SYSTEM_EVENT"
    action: str = ""  # RETRY, ERROR, TIMEOUT, etc.
    reason: str = ""  # Why this event occurred


def event_factory(event_dict: dict) -> Event:
    """Create appropriate Event subclass from dict."""
    event_type = event_dict.get("type")

    if event_type == "COMMAND":
        return CommandEvent(**event_dict)
    elif event_type == "STATE_TRANSITION":
        return StateTransitionEvent(**event_dict)
    elif event_type == "FEEDBACK_EVENT":
        return FeedbackEvent(**event_dict)
    elif event_type == "SYSTEM_EVENT":
        return SystemEvent(**event_dict)
    else:
        # Fallback to base Event
        return Event(**event_dict)
