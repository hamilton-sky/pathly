"""Pure reducer function: (state, event) → new_state."""

from orchestrator.state import State
from orchestrator.events import Event
from orchestrator.constants import FSMState, Agent, FeedbackFile, Mode, Rigor
from orchestrator.utils import utc_now

# Maps (agent, from_state) → (fast_next_state, paused_next_state)
_AGENT_TRANSITIONS = {
    (Agent.ARCHITECT, FSMState.STORMING):  (FSMState.PLANNING,        FSMState.STORM_PAUSED),
    (Agent.PLANNER,   FSMState.PLANNING):  (FSMState.BUILDING,        FSMState.PLAN_PAUSED),
    (Agent.BUILDER,   FSMState.BUILDING):  (FSMState.REVIEWING,       FSMState.REVIEWING),
    (Agent.REVIEWER,  FSMState.REVIEWING): (FSMState.BUILDING,        FSMState.IMPLEMENT_PAUSED),
    (Agent.TESTER,    FSMState.TESTING):   (FSMState.RETRO,           FSMState.TEST_PAUSED),
    (Agent.QUICK,     FSMState.RETRO):     (FSMState.DONE,            FSMState.DONE),
}


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
        retry_count_by_key=state.retry_count_by_key,  # shared ref — replaced in RETRY branch only
        last_actor=state.last_actor,
        state_stack=list(state.state_stack),
        created_at=state.created_at,
        updated_at=utc_now(),
        event_count=state.event_count + 1,
        last_event_type=event.type,
    )

    if event.type == "COMMAND":
        new_state.current = FSMState.STORMING
        new_state.active_command = event.metadata.get("value", getattr(event, "value", ""))
        new_state.active_feature = event.metadata.get("feature", "")
        new_state.rigor = event.metadata.get("rigor", Rigor.STANDARD)
        new_state.mode = event.metadata.get("mode", Mode.INTERACTIVE)
        return new_state

    if event.type == "AGENT_DONE":
        agent = event.metadata.get("agent", getattr(event, "agent", ""))
        new_state.last_actor = agent
        key = (agent, state.current)
        if key in _AGENT_TRANSITIONS:
            fast_next, paused_next = _AGENT_TRANSITIONS[key]
            new_state.current = fast_next if state.mode == Mode.FAST else paused_next
        return new_state

    if event.type == "FILE_CREATED":
        file = event.metadata.get("file", getattr(event, "file", ""))
        new_state.state_stack = [*state.state_stack, state.current]
        new_state.active_feedback_file = file
        if file == FeedbackFile.HUMAN_QUESTIONS:
            new_state.current = FSMState.BLOCKED_ON_HUMAN
        else:
            new_state.current = FSMState.BLOCKED_ON_FEEDBACK
        return new_state

    if event.type == "FILE_DELETED":
        if new_state.state_stack:
            new_state.current = new_state.state_stack[-1]
            new_state.state_stack = new_state.state_stack[:-1]
        new_state.active_feedback_file = None
        return new_state

    if event.type == "NO_DIFF_DETECTED":
        new_state.current = FSMState.BLOCKED_ON_HUMAN
        return new_state

    if event.type == "IMPLEMENT_COMPLETE":
        new_state.current = FSMState.TESTING
        return new_state

    if event.type == "STATE_TRANSITION":
        to_state = event.metadata.get("to_state", getattr(event, "to_state", ""))
        if to_state:
            new_state.current = to_state
        return new_state

    if event.type == "SYSTEM_EVENT":
        action = event.metadata.get("action", getattr(event, "action", ""))

        if action == "RETRY":
            retry_key = event.metadata.get("retry_key", "")
            if retry_key:
                new_retry = dict(new_state.retry_count_by_key)
                new_retry[retry_key] = new_retry.get(retry_key, 0) + 1
                new_state.retry_count_by_key = new_retry
            return new_state

        if action in ("ERROR", "TIMEOUT"):
            new_state.current = FSMState.BLOCKED_ON_HUMAN
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
