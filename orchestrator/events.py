"""Event types and schema for the event-sourced orchestrator."""

from dataclasses import dataclass, asdict, field, fields
from typing import Optional
from .constants import Events
import json
from .utils import utc_now


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

    type: str = Events.COMMAND
    value: str = ""  # the raw command string


@dataclass
class AgentDoneEvent(Event):
    """AGENT_DONE: An agent finished its work."""

    type: str = Events.AGENT_DONE
    agent: str = ""          # e.g. "architect", "planner", "builder", "reviewer", "tester", "quick"
    model: str = ""          # model used, e.g. "claude-opus-4-7", "claude-sonnet-4-6"
    tokens_in: int = 0       # input tokens consumed
    tokens_out: int = 0      # output tokens produced
    cost_usd: float = 0.0    # USD cost for this agent run (0.0 = not tracked)


@dataclass
class FileCreatedEvent(Event):
    """FILE_CREATED: A feedback file appeared on disk."""

    type: str = Events.FILE_CREATED
    file: str = ""  # e.g. "REVIEW_FAILURES.md"


@dataclass
class FileDeletedEvent(Event):
    """FILE_DELETED: A feedback file was resolved and removed."""

    type: str = Events.FILE_DELETED
    file: str = ""  # e.g. "REVIEW_FAILURES.md"


@dataclass
class HumanResponseEvent(Event):
    """HUMAN_RESPONSE: User chose a direction at a pause point."""

    type: str = Events.HUMAN_RESPONSE
    value: str = ""  # e.g. "yes", "no", "go", "stop", "continue", "fix", "done"


@dataclass
class NoDiffDetectedEvent(Event):
    """NO_DIFF_DETECTED: Builder finished but produced zero git diff (stall)."""

    type: str = Events.NO_DIFF_DETECTED


@dataclass
class ImplementCompleteEvent(Event):
    """IMPLEMENT_COMPLETE: All conversations in PROGRESS.md are done."""

    type: str = Events.IMPLEMENT_COMPLETE


@dataclass
class StateTransitionEvent(Event):
    """STATE_TRANSITION: Explicit FSM state move."""

    type: str = Events.STATE_TRANSITION
    from_state: str = ""
    to_state: str = ""


@dataclass
class SystemEvent(Event):
    """SYSTEM_EVENT: Internal system events (retry, error, timeout)."""

    type: str = Events.SYSTEM_EVENT
    action: str = ""   # RETRY, ERROR, TIMEOUT
    reason: str = ""   # Why this event occurred


_EVENT_CLASSES = {
    Events.COMMAND:            CommandEvent,
    Events.AGENT_DONE:         AgentDoneEvent,
    Events.FILE_CREATED:       FileCreatedEvent,
    Events.FILE_DELETED:       FileDeletedEvent,
    Events.HUMAN_RESPONSE:     HumanResponseEvent,
    Events.NO_DIFF_DETECTED:   NoDiffDetectedEvent,
    Events.IMPLEMENT_COMPLETE: ImplementCompleteEvent,
    Events.STATE_TRANSITION:   StateTransitionEvent,
    Events.SYSTEM_EVENT:       SystemEvent,
}


def event_factory(event_dict: dict) -> Event:
    """Create appropriate Event subclass from dict."""
    cls = _EVENT_CLASSES.get(event_dict.get("type"), Event)
    allowed = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in event_dict.items() if k in allowed})
