"""State management for the event-driven FSM orchestrator."""

from dataclasses import dataclass, field
from typing import Optional
from .constants import FSMState, Mode, Rigor
from .utils import utc_now


@dataclass
class State:
    """FSM state object. Reducer produces a new instance per event — never mutates in place."""

    current: str = FSMState.IDLE

    # Tracking active work
    active_command: Optional[str] = None
    active_feature: Optional[str] = None
    active_feedback_file: Optional[str] = None

    # Workflow configuration
    rigor: str = Rigor.STANDARD
    mode: str = Mode.INTERACTIVE

    # Retry tracking: key is "conv-N:FEEDBACK_FILE", value is retry count
    retry_count_by_key: dict = field(default_factory=dict)

    # Actor and history tracking
    last_actor: Optional[str] = None
    # Stack of states before BLOCKED transitions — supports nested blocks
    state_stack: list = field(default_factory=list)
    # Parallel stack mirroring state_stack — stores the active_feedback_file
    # value at the moment of each push, so unwinding can restore it.
    # Invariant: len(feedback_stack) == len(state_stack) at all times.
    feedback_stack: list = field(default_factory=list)

    # Timestamps
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

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
            "state_stack": self.state_stack,
            "feedback_stack": self.feedback_stack,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "event_count": self.event_count,
            "last_event_type": self.last_event_type,
        }


def initial_state() -> State:
    """Return a fresh initial state."""
    return State()
