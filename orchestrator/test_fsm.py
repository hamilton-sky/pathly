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
    StateTransitionEvent,
    FeedbackEvent,
    SystemEvent,
)
from orchestrator.reducer import reduce, reconstruct
from orchestrator.eventlog import EventLog


def test_command_event():
    """Test: COMMAND event moves state to STORMING."""
    state = initial_state()
    assert state.current == "IDLE"

    event = CommandEvent(
        name="/team-flow",
        feature="auth-service",
        metadata={"name": "/team-flow", "feature": "auth-service"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "STORMING"
    assert new_state.active_command == "/team-flow"
    assert new_state.active_feature == "auth-service"
    assert new_state.event_count == 1
    print("✅ test_command_event passed")


def test_feedback_open_blocks():
    """Test: FEEDBACK_EVENT with status=OPEN blocks and tracks file."""
    state = State(current="IMPLEMENTING")

    event = FeedbackEvent(
        status="OPEN",
        file="src/auth.py",
        message="Missing error handling",
        metadata={"status": "OPEN", "file": "src/auth.py"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "BLOCKED"
    assert new_state.active_feedback_file == "src/auth.py"
    assert new_state.event_count == 1
    print("✅ test_feedback_open_blocks passed")


def test_feedback_resolved_resumes():
    """Test: FEEDBACK_EVENT with status=RESOLVED moves back to IMPLEMENTING."""
    state = State(current="BLOCKED", active_feedback_file="src/auth.py")

    event = FeedbackEvent(
        status="RESOLVED",
        file="src/auth.py",
        message="Fixed",
        metadata={"status": "RESOLVED", "file": "src/auth.py"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "IMPLEMENTING"
    assert new_state.active_feedback_file is None
    print("✅ test_feedback_resolved_resumes passed")


def test_system_error_blocks():
    """Test: SYSTEM_EVENT with action=ERROR moves to BLOCKED."""
    state = State(current="STORMING")

    event = SystemEvent(
        action="ERROR",
        reason="Agent crashed",
        metadata={"action": "ERROR", "reason": "Agent crashed"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "BLOCKED"
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
    """Test: STATE_TRANSITION event moves explicitly."""
    state = State(current="STORMING")

    event = StateTransitionEvent(
        from_state="STORMING",
        to_state="IMPLEMENTING",
        metadata={"from_state": "STORMING", "to_state": "IMPLEMENTING"},
    )
    new_state = reduce(state, event)

    assert new_state.current == "IMPLEMENTING"
    print("✅ test_state_transition_event passed")


def test_reconstruct_idempotent():
    """Test: Reconstruction is idempotent (same result when run twice)."""
    events = [
        CommandEvent(
            name="/team-flow",
            feature="api",
            metadata={"name": "/team-flow", "feature": "api"},
        ),
        StateTransitionEvent(
            from_state="STORMING",
            to_state="IMPLEMENTING",
            metadata={"from_state": "STORMING", "to_state": "IMPLEMENTING"},
        ),
        FeedbackEvent(
            status="OPEN",
            file="src/main.py",
            message="Bug found",
            metadata={"status": "OPEN", "file": "src/main.py"},
        ),
    ]

    # Reconstruct twice
    state1 = reconstruct(events)
    state2 = reconstruct(events)

    # Should be identical
    assert state1.current == state2.current == "BLOCKED"
    assert state1.active_feedback_file == state2.active_feedback_file == "src/main.py"
    assert state1.event_count == state2.event_count == 3
    print("✅ test_reconstruct_idempotent passed")


def test_eventlog_persist_and_read():
    """Test: EventLog persists and reads events correctly."""
    # Use temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        filepath = f.name

    try:
        log = EventLog(filepath=filepath)

        # Append events
        event1 = CommandEvent(
            name="/test",
            feature="feature1",
            metadata={"name": "/test", "feature": "feature1"},
        )
        event2 = StateTransitionEvent(
            from_state="IDLE",
            to_state="STORMING",
            metadata={"from_state": "IDLE", "to_state": "STORMING"},
        )

        log.append(event1)
        log.append(event2)

        # Read back
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

        # Simulate workflow
        events_to_append = [
            CommandEvent(
                name="/team-flow",
                feature="backend",
                metadata={"name": "/team-flow", "feature": "backend"},
            ),
            StateTransitionEvent(
                from_state="STORMING",
                to_state="IMPLEMENTING",
                metadata={"from_state": "STORMING", "to_state": "IMPLEMENTING"},
            ),
            FeedbackEvent(
                status="RESOLVED",
                file="src/api.py",
                message="Fixed",
                metadata={"status": "RESOLVED", "file": "src/api.py"},
            ),
        ]

        for event in events_to_append:
            log.append(event)

        # Reconstruct from disk
        state1 = log.reconstruct_state()
        state2 = log.reconstruct_state()  # Do it again

        # Should match
        assert state1.to_dict() == state2.to_dict()
        assert state1.current == "IMPLEMENTING"
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
    test_feedback_open_blocks()
    test_feedback_resolved_resumes()
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
