"""Event types and schema for the event-sourced orchestrator."""

from dataclasses import dataclass, asdict, field
from typing import Optional
import json
from orchestrator.utils import utc_now


@dataclass
class Event:
    """Base event class. All events are immutable once created."""

    type: str
    timestamp: str = field(default_factory=utc_now)
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
    """COMMAND: User initiates a workflow command (e.g. /team-flow)."""

    type: str = "COMMAND"
    value: str = ""  # the raw command string


@dataclass
class AgentDoneEvent(Event):
    """AGENT_DONE: An agent finished its work."""

    type: str = "AGENT_DONE"
    agent: str = ""  # e.g. "architect", "planner", "builder", "reviewer", "tester", "quick"


@dataclass
class FileCreatedEvent(Event):
    """FILE_CREATED: A feedback file appeared on disk."""

    type: str = "FILE_CREATED"
    file: str = ""  # e.g. "REVIEW_FAILURES.md"


@dataclass
class FileDeletedEvent(Event):
    """FILE_DELETED: A feedback file was resolved and removed."""

    type: str = "FILE_DELETED"
    file: str = ""  # e.g. "REVIEW_FAILURES.md"


@dataclass
class HumanResponseEvent(Event):
    """HUMAN_RESPONSE: User chose a direction at a pause point."""

    type: str = "HUMAN_RESPONSE"
    value: str = ""  # e.g. "yes", "no", "go", "stop", "continue", "fix", "done"


@dataclass
class NoDiffDetectedEvent(Event):
    """NO_DIFF_DETECTED: Builder finished but produced zero git diff (stall)."""

    type: str = "NO_DIFF_DETECTED"


@dataclass
class ImplementCompleteEvent(Event):
    """IMPLEMENT_COMPLETE: All conversations in PROGRESS.md are done."""

    type: str = "IMPLEMENT_COMPLETE"


@dataclass
class StateTransitionEvent(Event):
    """STATE_TRANSITION: Explicit FSM state move."""

    type: str = "STATE_TRANSITION"
    from_state: str = ""
    to_state: str = ""


@dataclass
class SystemEvent(Event):
    """SYSTEM_EVENT: Internal system events (retry, error, timeout)."""

    type: str = "SYSTEM_EVENT"
    action: str = ""   # RETRY, ERROR, TIMEOUT
    reason: str = ""   # Why this event occurred


def event_factory(event_dict: dict) -> Event:
    """Create appropriate Event subclass from dict."""
    event_type = event_dict.get("type")

    if event_type == "COMMAND":
        return CommandEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata", "value")})
    elif event_type == "AGENT_DONE":
        return AgentDoneEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata", "agent")})
    elif event_type == "FILE_CREATED":
        return FileCreatedEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata", "file")})
    elif event_type == "FILE_DELETED":
        return FileDeletedEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata", "file")})
    elif event_type == "HUMAN_RESPONSE":
        return HumanResponseEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata", "value")})
    elif event_type == "NO_DIFF_DETECTED":
        return NoDiffDetectedEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata")})
    elif event_type == "IMPLEMENT_COMPLETE":
        return ImplementCompleteEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata")})
    elif event_type == "STATE_TRANSITION":
        return StateTransitionEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata", "from_state", "to_state")})
    elif event_type == "SYSTEM_EVENT":
        return SystemEvent(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata", "action", "reason")})
    else:
        return Event(**{k: v for k, v in event_dict.items() if k in ("type", "timestamp", "metadata")})
