"""Tests for pathly-engine CLI commands (go / status / doctor)."""
import json
import sys
from pathlib import Path

import pytest

from engine_cli.manager import cmd_go, cmd_status, cmd_doctor, _find_plans_dir


@pytest.fixture
def feature_dir(tmp_path):
    """Set up a fake plans/<feature>/ with STATE.json and EVENTS.jsonl."""
    plans = tmp_path / "plans"
    feat = plans / "my-feature"
    feat.mkdir(parents=True)
    state = {
        "current": "BUILDING",
        "active_feature": "my-feature",
        "rigor": "standard",
        "last_actor": "builder",
        "event_count": 3,
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    (feat / "STATE.json").write_text(json.dumps(state, indent=2))
    events = [
        {"type": "COMMAND", "timestamp": "2026-01-01T00:00:00+00:00", "metadata": {"value": "init"}},
    ]
    (feat / "EVENTS.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return feat


def test_go_appends_event(feature_dir, monkeypatch, capsys):
    plans = feature_dir.parent
    monkeypatch.setattr("engine_cli.manager._find_plans_dir", lambda: plans)
    cmd_go("add password reset")
    out = capsys.readouterr().out
    assert "my-feature" in out
    assert "BUILDING" in out
    assert "add password reset" in out
    # event appended
    lines = (feature_dir / "EVENTS.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    last = json.loads(lines[-1])
    assert last["type"] == "COMMAND"
    assert last["metadata"]["value"] == "add password reset"
    assert last["metadata"]["source"] == "pathly-go"


def test_go_exits_when_no_feature(tmp_path, monkeypatch):
    empty_plans = tmp_path / "plans"
    empty_plans.mkdir()
    monkeypatch.setattr("engine_cli.manager._find_plans_dir", lambda: empty_plans)
    with pytest.raises(SystemExit):
        cmd_go("add password reset")


def test_status_prints_state(feature_dir, monkeypatch, capsys):
    plans = feature_dir.parent
    monkeypatch.setattr("engine_cli.manager._find_plans_dir", lambda: plans)
    cmd_status()
    out = capsys.readouterr().out
    assert "my-feature" in out
    assert "BUILDING" in out
    assert "standard" in out
    assert "builder" in out


def test_status_named_feature(feature_dir, monkeypatch, capsys):
    plans = feature_dir.parent
    monkeypatch.setattr("engine_cli.manager._find_plans_dir", lambda: plans)
    cmd_status("my-feature")
    out = capsys.readouterr().out
    assert "my-feature" in out


def test_status_exits_for_unknown_feature(feature_dir, monkeypatch):
    plans = feature_dir.parent
    monkeypatch.setattr("engine_cli.manager._find_plans_dir", lambda: plans)
    with pytest.raises(SystemExit):
        cmd_status("nonexistent-feature")


def test_doctor_passes(feature_dir, monkeypatch, capsys):
    plans = feature_dir.parent
    monkeypatch.setattr("engine_cli.manager._find_plans_dir", lambda: plans)
    cmd_doctor()
    out = capsys.readouterr().out
    assert "All checks passed" in out
    assert "[PASS]" in out


def test_doctor_fails_missing_state(tmp_path, monkeypatch, capsys):
    plans = tmp_path / "plans"
    feat = plans / "broken-feature"
    feat.mkdir(parents=True)
    # no STATE.json, no EVENTS.jsonl
    monkeypatch.setattr("engine_cli.manager._find_plans_dir", lambda: plans)
    with pytest.raises(SystemExit):
        cmd_doctor()
    out = capsys.readouterr().out
    assert "[FAIL]" in out


def test_doctor_fails_corrupt_events(feature_dir, monkeypatch, capsys):
    (feature_dir / "EVENTS.jsonl").write_text("not-valid-json\n")
    plans = feature_dir.parent
    monkeypatch.setattr("engine_cli.manager._find_plans_dir", lambda: plans)
    with pytest.raises(SystemExit):
        cmd_doctor()
    out = capsys.readouterr().out
    assert "[FAIL]" in out
