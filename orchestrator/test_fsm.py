"""Tests for the event-driven FSM orchestrator."""

import os
import sys
import tempfile
from datetime import datetime

# Add orchestrator to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.state import State, initial_state
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
    assert state.current == "IDLE"

    event = CommandEvent(
        value="/team-flow auth-service",
        metadata={"value": "/team-flow auth-service", "feature": "auth-service"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "STORMING"
    assert new_state.active_feature == "auth-service"
    assert new_state.event_count == 1
    print("✅ test_command_event passed")


def test_file_created_blocks():
    """Test: FILE_CREATED event blocks workflow and tracks file."""
    state = State(current="BUILDING")

    event = FileCreatedEvent(
        file="REVIEW_FAILURES.md",
        metadata={"file": "REVIEW_FAILURES.md"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "BLOCKED_ON_FEEDBACK"
    assert new_state.active_feedback_file == "REVIEW_FAILURES.md"
    assert new_state.previous_state == "BUILDING"
    assert new_state.event_count == 1
    print("✅ test_file_created_blocks passed")


def test_file_deleted_resumes():
    """Test: FILE_DELETED event restores previous state."""
    state = State(
        current="BLOCKED_ON_FEEDBACK",
        active_feedback_file="REVIEW_FAILURES.md",
        previous_state="BUILDING",
    )

    event = FileDeletedEvent(
        file="REVIEW_FAILURES.md",
        metadata={"file": "REVIEW_FAILURES.md"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "BUILDING"
    assert new_state.active_feedback_file is None
    print("✅ test_file_deleted_resumes passed")


def test_system_error_blocks():
    """Test: SYSTEM_EVENT with action=ERROR moves to BLOCKED_ON_HUMAN."""
    state = State(current="STORMING")

    event = SystemEvent(
        action="ERROR",
        reason="Agent crashed",
        metadata={"action": "ERROR", "reason": "Agent crashed"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "BLOCKED_ON_HUMAN"
    print("✅ test_system_error_blocks passed")


def test_system_retry_noop():
    """Test: SYSTEM_EVENT with action=RETRY has no state change."""
    state = State(current="STORMING")

    event = SystemEvent(
        action="RETRY",
        reason="Transient failure",
        metadata={"action": "RETRY", "reason": "Transient failure"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "STORMING"
    assert new_state.event_count == 1
    print("✅ test_system_retry_noop passed")


def test_state_transition_event():
    """Test: STATE_TRANSITION event moves explicitly to target state."""
    state = State(current="STORMING")

    event = StateTransitionEvent(
        from_state="STORMING",
        to_state="BUILDING",
        metadata={"from_state": "STORMING", "to_state": "BUILDING"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "BUILDING"
    print("✅ test_state_transition_event passed")


def test_reconstruct_idempotent():
    """Test: Reconstruction is idempotent (same result when run twice)."""
    events = [
        CommandEvent(
            value="/team-flow api",
            metadata={"value": "/team-flow api", "feature": "api"},
        ),
        StateTransitionEvent(
            from_state="STORMING",
            to_state="BUILDING",
            metadata={"from_state": "STORMING", "to_state": "BUILDING"},
        ),
        FileCreatedEvent(
            file="REVIEW_FAILURES.md",
            metadata={"file": "REVIEW_FAILURES.md"},
        ),
    ]

    state1 = reconstruct(events)
    state2 = reconstruct(events)

    assert state1.current == state2.current == "BLOCKED_ON_FEEDBACK"
    assert state1.active_feedback_file == state2.active_feedback_file == "REVIEW_FAILURES.md"
    assert state1.event_count == state2.event_count == 3
    print("✅ test_reconstruct_idempotent passed")


def test_eventlog_persist_and_read():
    """Test: EventLog persists and reads events correctly."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        filepath = f.name

    try:
        log = EventLog(filepath=filepath)

        event1 = CommandEvent(
            value="/test",
            metadata={"value": "/test", "feature": "feature1"},
        )
        event2 = StateTransitionEvent(
            from_state="IDLE",
            to_state="STORMING",
            metadata={"from_state": "IDLE", "to_state": "STORMING"},
        )

        log.append(event1)
        log.append(event2)

        events = log.read_all()
        assert len(events) == 2
        assert events[0].type == "COMMAND"
        assert events[1].type == "STATE_TRANSITION"
        print("✅ test_eventlog_persist_and_read passed")

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


def test_eventlog_reconstruct_full_cycle():
    """Test: EventLog reconstruct is idempotent across persist cycle."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        filepath = f.name

    try:
        log = EventLog(filepath=filepath)

        events_to_append = [
            CommandEvent(
                value="/team-flow backend",
                metadata={"value": "/team-flow backend", "feature": "backend"},
            ),
            StateTransitionEvent(
                from_state="STORMING",
                to_state="BUILDING",
                metadata={"from_state": "STORMING", "to_state": "BUILDING"},
            ),
            FileDeletedEvent(
                file="REVIEW_FAILURES.md",
                metadata={"file": "REVIEW_FAILURES.md"},
            ),
        ]

        for event in events_to_append:
            log.append(event)

        state1 = log.reconstruct_state()
        state2 = log.reconstruct_state()

        # Compare all fields except timestamps (which differ between replays)
        d1 = {k: v for k, v in state1.to_dict().items() if k not in ("created_at", "updated_at")}
        d2 = {k: v for k, v in state2.to_dict().items() if k not in ("created_at", "updated_at")}
        assert d1 == d2
        assert state1.current == "BUILDING"
        assert state1.event_count == 3
        print("✅ test_eventlog_reconstruct_full_cycle passed")

    finally:
        if os.path.exists(filepath):
            os.remove(filepath)


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Running Minimal FSM Tests (Phase 1)")
    print("=" * 60)

    test_command_event()
    test_file_created_blocks()
    test_file_deleted_resumes()
    test_system_error_blocks()
    test_system_retry_noop()
    test_state_transition_event()
    test_reconstruct_idempotent()
    test_eventlog_persist_and_read()
    test_eventlog_reconstruct_full_cycle()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED (9/9)")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
