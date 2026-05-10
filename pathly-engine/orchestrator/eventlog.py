"""Append-only event log backed by EVENTS.jsonl."""

import os
import json
import tempfile
from typing import List, Optional
from .events import Event, event_factory
from .reducer import reconstruct
from .state import State


class EventLog:
    """Append-only event log. Single source of truth."""

    def __init__(
        self,
        filepath: Optional[str] = None,
        feature: Optional[str] = None,
        base_path: str = "plans",
    ):
        if filepath is not None:
            # Explicit path — used in tests and legacy callers
            self.filepath = filepath
        elif feature is not None:
            self.filepath = os.path.join(base_path, feature, "EVENTS.jsonl")
        else:
            # Fallback: default location (backward-compat with old default)
            self.filepath = os.path.join("orchestrator", "EVENTS.jsonl")

    def append(self, event: Event) -> None:
        """Append a single event to the log."""
        directory = os.path.dirname(self.filepath)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.filepath, "a") as f:
            f.write(event.to_jsonl() + "\n")

    def read_all(self) -> List[Event]:
        """Read all events from the log in order."""
        try:
            with open(self.filepath, "r") as f:
                return [
                    event_factory(json.loads(line))
                    for line in f
                    if line.strip()
                ]
        except FileNotFoundError:
            return []

    def reconstruct_state(self) -> State:
        """Replay all events to reconstruct current state."""
        events = self.read_all()
        return reconstruct(events)

    def write_state_json(self, state: State) -> None:
        """Atomically write current state to STATE.json alongside EVENTS.jsonl."""
        directory = os.path.dirname(self.filepath) or "."
        os.makedirs(directory, exist_ok=True)
        state_path = os.path.join(directory, "STATE.json")
        fd, tmp_path = tempfile.mkstemp(prefix="STATE.", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2)
                f.write("\n")
            os.replace(tmp_path, state_path)
        except Exception:
            try:
                os.remove(tmp_path)
            except FileNotFoundError:
                pass
            raise

    def recover(self) -> State:
        """Reconstruct from event log and reconcile with STATE.json.

        EVENTS.jsonl is authoritative. If STATE.json disagrees, it is rewritten
        from the replayed state so the two files are consistent again.
        """
        canonical = self.reconstruct_state()
        directory = os.path.dirname(self.filepath) or "."
        state_path = os.path.join(directory, "STATE.json")
        if os.path.exists(state_path):
            try:
                with open(state_path, encoding="utf-8") as f:
                    cached = json.load(f)
                if cached.get("current") != canonical.current:
                    # Event log wins — rewrite snapshot
                    self.write_state_json(canonical)
            except (json.JSONDecodeError, OSError):
                self.write_state_json(canonical)
        return canonical

    def clear(self) -> None:
        """Clear the event log (for testing only)."""
        try:
            os.remove(self.filepath)
        except FileNotFoundError:
            pass
