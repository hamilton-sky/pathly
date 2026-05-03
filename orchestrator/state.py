"""State management for the event-driven FSM orchestrator."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class State:
    """Immutable state object representing orchestrator FSM state."""

    # Core FSM state — matches spec vocabulary exactly
    # Valid values: IDLE, STORMING, STORM_PAUSED, PLANNING, PLAN_PAUSED,
    # BUILDING, REVIEWING, IMPLEMENT_PAUSED, TESTING, TEST_PAUSED,
    # RETRO, BLOCKED_ON_FEEDBACK, BLOCKED_ON_HUMAN, DONE
    current: str = "IDLE"

    # Tracking active work
    active_command: Optional[str] = None
    active_feature: Optional[str] = None
    active_feedback_file: Optional[str] = None

    # Workflow configuration
    rigor: str = "standard"   # "lite", "standard", "strict"
    mode: str = "interactive"  # "interactive", "fast"

    # Retry tracking: key is "conv-N:FEEDBACK_FILE", value is retry count
    retry_count_by_key: dict = field(default_factory=dict)

    # Actor and history tracking
    last_actor: Optional[str] = None
    previous_state: Optional[str] = None  # state before last BLOCKED transition

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now(datetime.UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(datetime.UTC).isoformat())

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
            "rigor": self.rigor,
            "mode": self.mode,
            "retry_count_by_key": self.retry_count_by_key,
            "last_actor": self.last_actor,
            "previous_state": self.previous_state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "event_count": self.event_count,
            "last_event_type": self.last_event_type,
        }


def initial_state() -> State:
    """Return a fresh initial state."""
    return State()
