"""State management for the event-driven FSM orchestrator."""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class State:
    """Immutable state object representing orchestrator FSM state."""

    # Core FSM state
    current: str = "IDLE"  # IDLE -> STORMING -> IMPLEMENTING -> BLOCKED -> (feedback loop)

    # Tracking active work
    active_command: Optional[str] = None
    active_feature: Optional[str] = None
    active_feedback_file: Optional[str] = None

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Event tracking
    event_count: int = 0
    last_event_type: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert state to dictionary for logging."""
        return {
            "current": self.current,
            "active_command": self.active_command,
            "active_feature": self.active_feature,
            "active_feedback_file": self.active_feedback_file,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "event_count": self.event_count,
            "last_event_type": self.last_event_type,
        }


def initial_state() -> State:
    """Return a fresh initial state."""
    return State()
