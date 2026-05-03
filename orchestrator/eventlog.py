"""Append-only event log backed by EVENTS.jsonl."""

import os
import json
from typing import List
from orchestrator.events import Event, event_factory
from orchestrator.reducer import reconstruct
from orchestrator.state import State


class EventLog:
    """Append-only event log. Single source of truth."""

    def __init__(self, filepath: str = "orchestrator/EVENTS.jsonl"):
        self.filepath = filepath
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

    def append(self, event: Event) -> None:
        """Append a single event to the log.

        Args:
            event: Event object to append
        """
        with open(self.filepath, "a") as f:
            f.write(event.to_jsonl() + "\n")

    def read_all(self) -> List[Event]:
        """Read all events from the log in order.

        Returns:
            List of Event objects (order preserved)
        """
        if not os.path.exists(self.filepath):
            return []

        events = []
        with open(self.filepath, "r") as f:
            for line in f:
                if line.strip():
                    event = event_factory(json.loads(line))
                    events.append(event)

        return events

    def reconstruct_state(self) -> State:
        """Replay all events to reconstruct current state.

        Returns:
            Final State after replaying all events
        """
        events = self.read_all()
        return reconstruct(events)

    def clear(self) -> None:
        """Clear the event log (for testing only)."""
        if os.path.exists(self.filepath):
            os.remove(self.filepath)
