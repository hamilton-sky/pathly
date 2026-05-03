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

    Event types: COMMAND, AGENT_DONE, FILE_CREATED, FILE_DELETED,
                 HUMAN_RESPONSE, NO_DIFF_DETECTED, IMPLEMENT_COMPLETE,
                 STATE_TRANSITION, SYSTEM_EVENT
    """

    new_state = State(
        current=state.current,
        active_command=state.active_command,
        active_feature=state.active_feature,
        active_feedback_file=state.active_feedback_file,
        rigor=state.rigor,
        mode=state.mode,
        retry_count_by_key=dict(state.retry_count_by_key),
        last_actor=state.last_actor,
        previous_state=state.previous_state,
        created_at=state.created_at,
        updated_at=datetime.utcnow().isoformat(),
        event_count=state.event_count + 1,
        last_event_type=event.type,
    )

    # === COMMAND ===
    if event.type == "COMMAND":
        new_state.current = "STORMING"
        new_state.active_command = event.metadata.get("value", getattr(event, "value", ""))
        new_state.active_feature = event.metadata.get("feature", "")
        new_state.rigor = event.metadata.get("rigor", "standard")
        new_state.mode = event.metadata.get("mode", "interactive")
        return new_state

    # === AGENT_DONE ===
    if event.type == "AGENT_DONE":
        agent = event.metadata.get("agent", getattr(event, "agent", ""))
        new_state.last_actor = agent

        if agent == "architect" and state.current == "STORMING":
            if state.mode == "fast":
                new_state.current = "PLANNING"
            else:
                new_state.current = "STORM_PAUSED"

        elif agent == "planner" and state.current == "PLANNING":
            if state.mode == "fast":
                new_state.current = "BUILDING"
            else:
                new_state.current = "PLAN_PAUSED"

        elif agent == "builder" and state.current == "BUILDING":
            new_state.current = "REVIEWING"

        elif agent == "reviewer" and state.current == "REVIEWING":
            if state.mode == "fast":
                new_state.current = "BUILDING"
            else:
                new_state.current = "IMPLEMENT_PAUSED"

        elif agent == "tester" and state.current == "TESTING":
            if state.mode == "fast":
                new_state.current = "RETRO"
            else:
                new_state.current = "TEST_PAUSED"

        elif agent == "quick" and state.current == "RETRO":
            new_state.current = "DONE"

        return new_state

    # === FILE_CREATED ===
    if event.type == "FILE_CREATED":
        file = event.metadata.get("file", getattr(event, "file", ""))
        new_state.previous_state = state.current
        new_state.active_feedback_file = file
        if file == "HUMAN_QUESTIONS.md":
            new_state.current = "BLOCKED_ON_HUMAN"
        else:
            new_state.current = "BLOCKED_ON_FEEDBACK"
        return new_state

    # === FILE_DELETED ===
    if event.type == "FILE_DELETED":
        # Restore the state we were in before the block
        if state.previous_state:
            new_state.current = state.previous_state
        new_state.active_feedback_file = None
        new_state.previous_state = None
        return new_state

    # === NO_DIFF_DETECTED ===
    if event.type == "NO_DIFF_DETECTED":
        new_state.current = "BLOCKED_ON_HUMAN"
        return new_state

    # === IMPLEMENT_COMPLETE ===
    if event.type == "IMPLEMENT_COMPLETE":
        new_state.current = "TESTING"
        return new_state

    # === STATE_TRANSITION ===
    if event.type == "STATE_TRANSITION":
        to_state = event.metadata.get("to_state", getattr(event, "to_state", ""))
        if to_state:
            new_state.current = to_state
        return new_state

    # === SYSTEM_EVENT ===
    if event.type == "SYSTEM_EVENT":
        action = event.metadata.get("action", getattr(event, "action", ""))

        if action == "RETRY":
            retry_key = event.metadata.get("retry_key", "")
            if retry_key:
                new_state.retry_count_by_key[retry_key] = (
                    new_state.retry_count_by_key.get(retry_key, 0) + 1
                )
            return new_state

        if action in ("ERROR", "TIMEOUT"):
            new_state.current = "BLOCKED_ON_HUMAN"
            return new_state

    return new_state


def reconstruct(events: list) -> State:
    """
    Rebuild state from event log.

    Idempotent: replaying the same events always produces the same state.

    Args:
        events: List of Event objects (in order)

    Returns:
        Final reconstructed State
    """
    state = State()

    for event in events:
        state = reduce(state, event)

    return state
