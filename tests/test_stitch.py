"""Tests for pathly.cli.stitch.stitch_agent."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from pathly.cli.stitch import stitch_agent


def _write(path: Path, text: str) -> Path:
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    return path


def test_happy_path(tmp_path):
    core = _write(tmp_path / "architect.md", """
        # Architect

        Behavioral contract body.
    """)
    meta = _write(tmp_path / "architect.yaml", """
        name: architect
        description: Technical architecture design.
        model: opus
        tools: [Read, Edit]
        can_spawn: [quick, scout]
        spawn_section: |
          ## Sub-agent invocation
          Agent(subagent_type="quick")
    """)
    result = stitch_agent(core, meta)
    assert "---" in result
    assert "name: architect" in result
    assert "model: opus" in result
    assert "tools: [Read, Edit]" in result
    assert "## Capabilities" in result
    assert "may spawn: quick, scout" in result
    assert "Behavioral contract body" in result
    assert "Sub-agent invocation" in result


def test_missing_core_raises(tmp_path):
    meta = _write(tmp_path / "quick.yaml", """
        name: quick
        description: Quick lookup.
        model: haiku
        can_spawn: []
        spawn_section: ""
    """)
    with pytest.raises(FileNotFoundError):
        stitch_agent(tmp_path / "missing.md", meta)


def test_malformed_yaml_raises(tmp_path):
    core = _write(tmp_path / "architect.md", "body\n")
    meta = tmp_path / "architect.yaml"
    meta.write_text(": bad: yaml: [\n", encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        stitch_agent(core, meta)


def test_can_spawn_all(tmp_path):
    core = _write(tmp_path / "orchestrator.md", "Orchestrator body.\n")
    meta = _write(tmp_path / "orchestrator.yaml", """
        name: orchestrator
        description: FSM orchestrator.
        model: opus
        can_spawn: all
        spawn_section: ""
    """)
    result = stitch_agent(core, meta)
    assert "may spawn any other agent type" in result


def test_can_spawn_empty_is_terminal(tmp_path):
    core = _write(tmp_path / "quick.md", "Quick body.\n")
    meta = _write(tmp_path / "quick.yaml", """
        name: quick
        description: Quick lookup.
        model: haiku
        can_spawn: []
        spawn_section: ""
    """)
    result = stitch_agent(core, meta)
    assert "TERMINAL" in result


def test_output_order(tmp_path):
    core = _write(tmp_path / "builder.md", "Builder core.\n")
    meta = _write(tmp_path / "builder.yaml", """
        name: builder
        description: Builds things.
        model: sonnet
        can_spawn: [quick, scout]
        spawn_section: |
          ## Spawn section
          spawn here
    """)
    result = stitch_agent(core, meta)
    fm_end = result.index("---\n", 1)
    cap_pos = result.index("## Capabilities")
    core_pos = result.index("Builder core")
    spawn_pos = result.index("## Spawn section")
    assert fm_end < cap_pos < core_pos < spawn_pos
