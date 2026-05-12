"""Pure reducer function: (state, event) → new_state."""

from .state import State
from .events import Event
from .constants import FSMState, Agent, FeedbackFile, Mode, Rigor, Events, MAX_RETRIES
from .utils import utc_now

# Maps (agent, from_state) → (fast_next_state, paused_next_state)
_AGENT_TRANSITIONS = {
    (Agent.PO,         FSMState.PO_DISCUSSING): (FSMState.STORMING,      FSMState.PO_PAUSED),
    (Agent.EXPLORER,   FSMState.EXPLORING):     (FSMState.PLANNING,      FSMState.EXPLORE_PAUSED),
    (Agent.ARCHITECT,  FSMState.STORMING):      (FSMState.PLANNING,      FSMState.STORM_PAUSED),
    (Agent.PLANNER,    FSMState.PLANNING):    (FSMState.BUILDING,        FSMState.PLAN_PAUSED),
    (Agent.BUILDER,    FSMState.BUILDING):    (FSMState.REVIEWING,       FSMState.REVIEWING),  # reviewer always runs, no pause option
    (Agent.REVIEWER,   FSMState.REVIEWING):   (FSMState.BUILDING,        FSMState.IMPLEMENT_PAUSED),
    (Agent.TESTER,     FSMState.TESTING):     (FSMState.RETRO,           FSMState.TEST_PAUSED),
    (Agent.QUICK,      FSMState.RETRO):       (FSMState.DONE,            FSMState.DONE),
}

# Maps paused state → next state when human says "go"
# EXPLORE_PAUSED path A (plan) is default; paths B (nano/build) and C (stop) use STATE_TRANSITION
_HUMAN_TRANSITIONS = {
    FSMState.PO_PAUSED:        FSMState.STORMING,
    FSMState.EXPLORE_PAUSED:   FSMState.PLANNING,
    FSMState.STORM_PAUSED:     FSMState.PLANNING,
    FSMState.PLAN_PAUSED:      FSMState.BUILDING,
    FSMState.IMPLEMENT_PAUSED: FSMState.BUILDING,
    FSMState.TEST_PAUSED:      FSMState.RETRO,
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
        retry_count_by_key=dict(state.retry_count_by_key),
        last_actor=state.last_actor,
        state_stack=list(state.state_stack),
        feedback_stack=list(state.feedback_stack),
        created_at=state.created_at,
        updated_at=utc_now(),
        event_count=state.event_count + 1,
        last_event_type=event.type,
    )

    if event.type == Events.COMMAND:
        entry_state = event.metadata.get("entry_state", FSMState.STORMING)
        new_state.current = entry_state
        new_state.active_command = getattr(event, "value", "")
        new_state.active_feature = event.metadata.get("feature", "")
        new_state.rigor = event.metadata.get("rigor", Rigor.STANDARD)
        new_state.mode = event.metadata.get("mode", Mode.INTERACTIVE)
        return new_state

    if event.type == Events.AGENT_DONE:
        agent = getattr(event, "agent", "")
        new_state.last_actor = agent
        key = (agent, state.current)
        if key in _AGENT_TRANSITIONS:
            fast_next, paused_next = _AGENT_TRANSITIONS[key]
            new_state.current = fast_next if state.mode == Mode.FAST else paused_next
        return new_state

    if event.type == Events.FILE_CREATED:
        file = getattr(event, "file", "")
        new_state.state_stack = [*state.state_stack, state.current]
        # Push the prior active_feedback_file BEFORE overwriting it,
        # so a later FILE_DELETED can restore it on unwind.
        new_state.feedback_stack = [*state.feedback_stack, state.active_feedback_file]
        new_state.active_feedback_file = file
        if file == FeedbackFile.HUMAN_QUESTIONS:
            new_state.current = FSMState.BLOCKED_ON_HUMAN
        else:
            new_state.current = FSMState.BLOCKED_ON_FEEDBACK
        return new_state

    if event.type == Events.FILE_DELETED:
        if new_state.state_stack:
            new_state.current = new_state.state_stack[-1]
            new_state.state_stack = new_state.state_stack[:-1]
        if new_state.feedback_stack:
            # Restore the active_feedback_file that was active before the push.
            new_state.active_feedback_file = new_state.feedback_stack[-1]
            new_state.feedback_stack = new_state.feedback_stack[:-1]
        else:
            new_state.active_feedback_file = None
        return new_state

    if event.type == Events.HUMAN_RESPONSE:
        if state.current in _HUMAN_TRANSITIONS:
            new_state.current = _HUMAN_TRANSITIONS[state.current]
        elif state.current == FSMState.BLOCKED_ON_HUMAN:
            # NO_DIFF_DETECTED path: human clears the stall, retry build
            new_state.current = FSMState.BUILDING
        return new_state

    if event.type == Events.NO_DIFF_DETECTED:
        new_state.current = FSMState.BLOCKED_ON_HUMAN
        return new_state

    if event.type == Events.IMPLEMENT_COMPLETE:
        new_state.current = FSMState.TESTING
        return new_state

    if event.type == Events.STATE_TRANSITION:
        to_state = getattr(event, "to_state", "")
        if to_state:
            new_state.current = to_state
        return new_state

    if event.type == Events.SYSTEM_EVENT:
        action = getattr(event, "action", "")

        if action == "RETRY":
            retry_key = event.metadata.get("retry_key", "")
            if retry_key:
                new_retry = dict(new_state.retry_count_by_key)
                new_retry[retry_key] = new_retry.get(retry_key, 0) + 1
                new_state.retry_count_by_key = new_retry
                if new_retry[retry_key] >= MAX_RETRIES:
                    new_state.current = FSMState.BLOCKED_ON_HUMAN
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
