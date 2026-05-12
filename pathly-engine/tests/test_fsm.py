"""Tests for the event-driven FSM orchestrator."""

from orchestrator.state import State, initial_state
from orchestrator.constants import FSMState, Agent, FeedbackFile, Mode, Rigor
from orchestrator.events import (
    CommandEvent,
    AgentDoneEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    StateTransitionEvent,
    SystemEvent,
)
from orchestrator.reducer import reduce, reconstruct
from orchestrator.eventlog import EventLog


def test_command_event():
    """Test: COMMAND event moves state from IDLE to STORMING."""
    state = initial_state()
    assert state.current == FSMState.IDLE

    event = CommandEvent(
        value="/team-flow auth-service",
        metadata={"value": "/team-flow auth-service", "feature": "auth-service"},
    )
    new_state = reduce(state, event)

    assert new_state.current == FSMState.STORMING
    assert new_state.active_feature == "auth-service"
    assert new_state.event_count == 1


def test_command_event_rejects_invalid_metadata():
    state = initial_state()

    for metadata in (
        {"rigor": "garbage"},
        {"mode": "garbage"},
        {"entry_state": "garbage"},
    ):
        event = CommandEvent(value="/team-flow auth-service", metadata=metadata)

        assert reduce(state, event).current == FSMState.BLOCKED_ON_HUMAN


def test_command_event_accepts_valid_metadata():
    state = initial_state()
    event = CommandEvent(
        value="/team-flow auth-service",
        metadata={
            "feature": "auth-service",
            "rigor": Rigor.LITE,
            "mode": Mode.FAST,
            "entry_state": FSMState.BUILDING,
        },
    )

    new_state = reduce(state, event)

    assert new_state.current == FSMState.BUILDING
    assert new_state.rigor == Rigor.LITE
    assert new_state.mode == Mode.FAST


def test_agent_done_rejects_invalid_agent_state_pair():
    state = State(current=FSMState.PLANNING)
    event = AgentDoneEvent(agent=Agent.BUILDER)

    new_state = reduce(state, event)

    assert new_state.current == FSMState.BLOCKED_ON_HUMAN


def test_file_created_blocks():
    """Test: FILE_CREATED event blocks workflow and tracks file."""
    state = State(current=FSMState.BUILDING)

    event = FileCreatedEvent(
        file=FeedbackFile.REVIEW_FAILURES,
        metadata={"file": FeedbackFile.REVIEW_FAILURES},
    )
    new_state = reduce(state, event)

    assert new_state.current == FSMState.BLOCKED_ON_FEEDBACK
    assert new_state.active_feedback_file == FeedbackFile.REVIEW_FAILURES
    assert new_state.state_stack == [FSMState.BUILDING]
    assert new_state.event_count == 1


def test_file_deleted_resumes():
    """Test: FILE_DELETED event restores previous state."""
    state = State(
        current=FSMState.BLOCKED_ON_FEEDBACK,
        active_feedback_file=FeedbackFile.REVIEW_FAILURES,
        state_stack=[FSMState.BUILDING],
    )

    event = FileDeletedEvent(
        file=FeedbackFile.REVIEW_FAILURES,
        metadata={"file": FeedbackFile.REVIEW_FAILURES},
    )
    new_state = reduce(state, event)

    assert new_state.current == FSMState.BUILDING
    assert new_state.active_feedback_file is None
    assert new_state.state_stack == []


def test_system_error_blocks():
    """Test: SYSTEM_EVENT with action=ERROR moves to BLOCKED_ON_HUMAN."""
    state = State(current=FSMState.STORMING)

    event = SystemEvent(
        action="ERROR",
        reason="Agent crashed",
        metadata={"action": "ERROR", "reason": "Agent crashed"},
    )
    new_state = reduce(state, event)

    assert new_state.current == FSMState.BLOCKED_ON_HUMAN


def test_system_retry_increments_count():
    """Test: SYSTEM_EVENT RETRY increments counter but keeps state below threshold."""
    state = State(current=FSMState.STORMING)

    event = SystemEvent(
        action="RETRY",
        reason="Transient failure",
        metadata={"action": "RETRY", "retry_key": "feat:REVIEW_FAILURES.md"},
    )
    new_state = reduce(state, event)

    assert new_state.current == FSMState.STORMING
    assert new_state.retry_count_by_key.get("feat:REVIEW_FAILURES.md") == 1
    assert new_state.event_count == 1


def test_system_retry_escalates_to_blocked_on_human():
    """Test: SYSTEM_EVENT RETRY escalates to BLOCKED_ON_HUMAN when MAX_RETRIES reached."""
    from orchestrator.constants import MAX_RETRIES

    state = State(current=FSMState.STORMING)
    retry_event = SystemEvent(
        action="RETRY",
        reason="Repeated failure",
        metadata={"action": "RETRY", "retry_key": "feat:REVIEW_FAILURES.md"},
    )
    for _ in range(MAX_RETRIES):
        state = reduce(state, retry_event)

    assert state.current == FSMState.BLOCKED_ON_HUMAN
    assert state.retry_count_by_key.get("feat:REVIEW_FAILURES.md") == MAX_RETRIES


def test_state_transition_event():
    """Test: STATE_TRANSITION event moves explicitly to target state."""
    state = State(current=FSMState.STORMING)

    event = StateTransitionEvent(
        from_state=FSMState.STORMING,
        to_state=FSMState.BUILDING,
        metadata={"from_state": FSMState.STORMING, "to_state": FSMState.BUILDING},
    )
    new_state = reduce(state, event)

    assert new_state.current == FSMState.BUILDING


def test_reconstruct_idempotent():
    """Test: Reconstruction is idempotent (same result when run twice)."""
    events = [
        CommandEvent(
            value="/team-flow api",
            metadata={"value": "/team-flow api", "feature": "api"},
        ),
        StateTransitionEvent(
            from_state=FSMState.STORMING,
            to_state=FSMState.BUILDING,
            metadata={"from_state": FSMState.STORMING, "to_state": FSMState.BUILDING},
        ),
        FileCreatedEvent(
            file=FeedbackFile.REVIEW_FAILURES,
            metadata={"file": FeedbackFile.REVIEW_FAILURES},
        ),
    ]

    state1 = reconstruct(events)
    state2 = reconstruct(events)

    assert state1.current == state2.current == FSMState.BLOCKED_ON_FEEDBACK
    assert state1.active_feedback_file == state2.active_feedback_file == FeedbackFile.REVIEW_FAILURES
    assert state1.event_count == state2.event_count == 3


def test_eventlog_persist_and_read(tmp_path):
    """Test: EventLog persists and reads events correctly."""
    filepath = str(tmp_path / "events.jsonl")
    log = EventLog(filepath=filepath)

    event1 = CommandEvent(
        value="/test",
        metadata={"value": "/test", "feature": "feature1"},
    )
    event2 = StateTransitionEvent(
        from_state=FSMState.IDLE,
        to_state=FSMState.STORMING,
        metadata={"from_state": FSMState.IDLE, "to_state": FSMState.STORMING},
    )

    log.append(event1)
    log.append(event2)

    events = log.read_all()
    assert len(events) == 2
    assert events[0].type == "COMMAND"
    assert events[1].type == "STATE_TRANSITION"


def test_eventlog_supports_filename_without_directory(tmp_path, monkeypatch):
    """Test: EventLog can write to a filename in the current directory."""
    monkeypatch.chdir(tmp_path)
    log = EventLog(filepath="events.jsonl")

    log.append(CommandEvent(
        value="/test",
        metadata={"value": "/test", "feature": "feature1"},
    ))

    assert (tmp_path / "events.jsonl").exists()
    assert len(log.read_all()) == 1


def test_eventlog_reconstruct_full_cycle(tmp_path):
    """Test: EventLog reconstruct is idempotent across persist cycle."""
    filepath = str(tmp_path / "events.jsonl")
    log = EventLog(filepath=filepath)

    events_to_append = [
        CommandEvent(
            value="/team-flow backend",
            metadata={"value": "/team-flow backend", "feature": "backend"},
        ),
        StateTransitionEvent(
            from_state=FSMState.STORMING,
            to_state=FSMState.BUILDING,
            metadata={"from_state": FSMState.STORMING, "to_state": FSMState.BUILDING},
        ),
        FileDeletedEvent(
            file=FeedbackFile.REVIEW_FAILURES,
            metadata={"file": FeedbackFile.REVIEW_FAILURES},
        ),
    ]

    for event in events_to_append:
        log.append(event)

    state1 = log.reconstruct_state()
    state2 = log.reconstruct_state()

    d1 = {k: v for k, v in state1.to_dict().items() if k not in ("created_at", "updated_at")}
    d2 = {k: v for k, v in state2.to_dict().items() if k not in ("created_at", "updated_at")}
    assert d1 == d2
    assert state1.current == FSMState.BUILDING
    assert state1.event_count == 3


def test_state_json_write_is_atomic(tmp_path):
    """STATE.json writes should leave only the final file after a successful write."""
    log = EventLog(filepath=str(tmp_path / "events.jsonl"))
    state = initial_state()

    log.write_state_json(state)

    state_path = tmp_path / "STATE.json"
    assert state_path.exists()
    assert not list(tmp_path.glob("STATE.*.tmp"))
    assert '"current": "IDLE"' in state_path.read_text(encoding="utf-8")


def test_deep_block_two_levels():
    """Test: BUILDING → BLOCKED_ON_FEEDBACK → BLOCKED_ON_HUMAN (two-level nesting)."""
    state = State(current=FSMState.BUILDING)

    state = reduce(state, FileCreatedEvent(
        file=FeedbackFile.REVIEW_FAILURES,
        metadata={"file": FeedbackFile.REVIEW_FAILURES},
    ))
    assert state.current == FSMState.BLOCKED_ON_FEEDBACK
    assert len(state.state_stack) == len(state.feedback_stack)
    assert state.state_stack == [FSMState.BUILDING]
    assert state.feedback_stack == [None]

    state = reduce(state, FileCreatedEvent(
        file=FeedbackFile.HUMAN_QUESTIONS,
        metadata={"file": FeedbackFile.HUMAN_QUESTIONS},
    ))
    assert state.current == FSMState.BLOCKED_ON_HUMAN
    assert state.active_feedback_file == FeedbackFile.HUMAN_QUESTIONS
    assert len(state.state_stack) == len(state.feedback_stack)
    assert state.state_stack == [FSMState.BUILDING, FSMState.BLOCKED_ON_FEEDBACK]
    assert state.feedback_stack == [None, FeedbackFile.REVIEW_FAILURES]


def test_deep_block_unwind_one_level():
    """Test: BLOCKED_ON_HUMAN → BLOCKED_ON_FEEDBACK when inner block resolves.

    On unwind, active_feedback_file is restored from feedback_stack to the outer
    block's value (REVIEW_FAILURES) rather than being cleared to None.
    """
    state = State(current=FSMState.BUILDING)
    state = reduce(state, FileCreatedEvent(
        file=FeedbackFile.REVIEW_FAILURES,
        metadata={"file": FeedbackFile.REVIEW_FAILURES},
    ))
    state = reduce(state, FileCreatedEvent(
        file=FeedbackFile.HUMAN_QUESTIONS,
        metadata={"file": FeedbackFile.HUMAN_QUESTIONS},
    ))

    state = reduce(state, FileDeletedEvent(
        file=FeedbackFile.HUMAN_QUESTIONS,
        metadata={"file": FeedbackFile.HUMAN_QUESTIONS},
    ))
    assert state.current == FSMState.BLOCKED_ON_FEEDBACK
    assert state.active_feedback_file == FeedbackFile.REVIEW_FAILURES
    assert len(state.state_stack) == len(state.feedback_stack)
    assert state.state_stack == [FSMState.BUILDING]
    assert state.feedback_stack == [None]


def test_deep_block_full_unwind():
    """Test: BUILDING → two-level block → full unwind back to BUILDING."""
    state = State(current=FSMState.BUILDING)

    state = reduce(state, FileCreatedEvent(
        file=FeedbackFile.REVIEW_FAILURES,
        metadata={"file": FeedbackFile.REVIEW_FAILURES},
    ))
    assert state.current == FSMState.BLOCKED_ON_FEEDBACK
    assert len(state.state_stack) == len(state.feedback_stack)
    assert state.state_stack == [FSMState.BUILDING]
    assert state.feedback_stack == [None]

    state = reduce(state, FileCreatedEvent(
        file=FeedbackFile.HUMAN_QUESTIONS,
        metadata={"file": FeedbackFile.HUMAN_QUESTIONS},
    ))
    assert state.current == FSMState.BLOCKED_ON_HUMAN
    assert len(state.state_stack) == len(state.feedback_stack)
    assert state.state_stack == [FSMState.BUILDING, FSMState.BLOCKED_ON_FEEDBACK]
    assert state.feedback_stack == [None, FeedbackFile.REVIEW_FAILURES]

    state = reduce(state, FileDeletedEvent(
        file=FeedbackFile.HUMAN_QUESTIONS,
        metadata={"file": FeedbackFile.HUMAN_QUESTIONS},
    ))
    assert state.current == FSMState.BLOCKED_ON_FEEDBACK
    assert state.active_feedback_file == FeedbackFile.REVIEW_FAILURES
    assert len(state.state_stack) == len(state.feedback_stack)
    assert state.state_stack == [FSMState.BUILDING]
    assert state.feedback_stack == [None]

    state = reduce(state, FileDeletedEvent(
        file=FeedbackFile.REVIEW_FAILURES,
        metadata={"file": FeedbackFile.REVIEW_FAILURES},
    ))
    assert state.current == FSMState.BUILDING
    assert state.active_feedback_file is None
    assert len(state.state_stack) == len(state.feedback_stack)
    assert state.state_stack == []
    assert state.feedback_stack == []
