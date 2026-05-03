"""Pure reducer function: (state, event) → new_state."""

from datetime import datetime
from orchestrator.state import State
from orchestrator.events import Event


def reduce(state: State, event: Event) -> State:
    """
    Pure function: reduce(state, event) → new_state

    This is the core FSM logic. No side effects, no agent calls.
    Input: current state + incoming event
    Output: new state

    Event types:
    - COMMAND: Initiate workflow
    - STATE_TRANSITION: Acknowledge FSM move
    - FEEDBACK_EVENT: Handle open/resolved feedback
    - SYSTEM_EVENT: Handle retry/error/timeout
    """

    # Create new state (immutable)
    new_state = State(
        current=state.current,
        active_command=state.active_command,
        active_feature=state.active_feature,
        active_feedback_file=state.active_feedback_file,
        created_at=state.created_at,
        updated_at=datetime.utcnow().isoformat(),
        event_count=state.event_count + 1,
        last_event_type=event.type,
    )

    # === COMMAND events ===
    if event.type == "COMMAND":
        # User kicks off a workflow
        new_state.current = "STORMING"
        new_state.active_command = event.metadata.get("name", "")
        new_state.active_feature = event.metadata.get("feature", "")
        return new_state

    # === FEEDBACK_EVENT ===
    if event.type == "FEEDBACK_EVENT":
        status = event.metadata.get("status", "")
        file = event.metadata.get("file", "")

        if status == "OPEN":
            # Feedback detected → block and hold
            new_state.current = "BLOCKED"
            new_state.active_feedback_file = file
            return new_state

        if status == "RESOLVED":
            # Feedback resolved → resume implementing
            new_state.current = "IMPLEMENTING"
            new_state.active_feedback_file = None
            return new_state

    # === STATE_TRANSITION ===
    if event.type == "STATE_TRANSITION":
        # Acknowledge explicit state move (e.g., STORMING → IMPLEMENTING)
        to_state = event.metadata.get("to_state", "")
        if to_state:
            new_state.current = to_state
        return new_state

    # === SYSTEM_EVENT ===
    if event.type == "SYSTEM_EVENT":
        action = event.metadata.get("action", "")

        if action == "RETRY":
            # Retry → stay in current state, let downstream handle it
            return new_state

        if action == "ERROR":
            # Error → block and wait for manual intervention
            new_state.current = "BLOCKED"
            return new_state

        if action == "TIMEOUT":
            # Timeout → block
            new_state.current = "BLOCKED"
            return new_state

    # If event type unrecognized, return state unchanged
    return new_state


def reconstruct(events: list) -> State:
    """
    Rebuild state from event log.

    This is the "truth engine": replay all events to get current state.
    Idempotent: running twice = same result.

    Args:
        events: List of Event objects (in order)

    Returns:
        Final reconstructed State
    """
    state = State()  # Start from initial state

    for event in events:
        state = reduce(state, event)

    return state
