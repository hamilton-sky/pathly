"""Tests for feedback file TTL and orphan detection in TeamFlowFiles.

All tests inject a fixed clock so results are deterministic and
never depend on wall-clock time.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from team_flow.filesystem import TeamFlowFiles
from team_flow.config import DriverConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(tmp_path: Path) -> DriverConfig:
    """Minimal DriverConfig pointing at a temp directory."""
    return DriverConfig(
        repo_root=tmp_path,
        feature="test-feature",
        mode="interactive",
        entry="discovery",
    )


def _write_feedback(
    feedback_dir: Path,
    filename: str,
    created_at: datetime,
    ttl_hours: float = 168,
    event_id: str = "evt-001",
) -> Path:
    """Write a feedback file with YAML frontmatter."""
    feedback_dir.mkdir(parents=True, exist_ok=True)
    content = (
        f"---\n"
        f"created_at: {created_at.isoformat()}\n"
        f"created_by_event: {event_id}\n"
        f"ttl_hours: {ttl_hours}\n"
        f"---\n"
        f"Some feedback content.\n"
    )
    path = feedback_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def _make_files(tmp_path: Path, clock) -> TeamFlowFiles:
    return TeamFlowFiles(_make_config(tmp_path), clock=clock)


def _fixed_clock(dt: datetime):
    return lambda: dt


# ---------------------------------------------------------------------------
# TTL tests
# ---------------------------------------------------------------------------

class TestTTLNotExpired:
    def test_fresh_file_is_valid(self, tmp_path):
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        created = now - timedelta(hours=12)
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "REVIEW_FAILURES.md", created, ttl_hours=168)
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert result == "", f"Expected no issue but got: {result}"

    def test_exactly_at_boundary_is_not_expired(self, tmp_path):
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        created = now - timedelta(hours=168)  # exactly at TTL boundary
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "TEST_FAILURES.md", created, ttl_hours=168)
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        # Exactly at boundary: created + ttl == now, not strictly greater, so not expired
        assert result == "", f"Expected no issue at boundary but got: {result}"

    def test_long_pause_does_not_false_positive(self, tmp_path):
        """User paused for 3 days — default 168h TTL should not fire."""
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        created = now - timedelta(days=3)  # 72 hours ago, well within 168h TTL
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "ARCH_FEEDBACK.md", created, ttl_hours=168)
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert result == "", f"Long pause caused false positive: {result}"

    def test_custom_ttl_respected(self, tmp_path):
        """A file with a short explicit TTL of 1h should not expire at 30 min."""
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        created = now - timedelta(minutes=30)
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "IMPL_QUESTIONS.md", created, ttl_hours=1)
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert result == ""


class TestTTLExpired:
    def test_expired_file_is_flagged(self, tmp_path):
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        created = now - timedelta(hours=169)  # 1 hour past default TTL
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "REVIEW_FAILURES.md", created, ttl_hours=168)
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert "TTL expired" in result

    def test_expired_message_contains_creation_time(self, tmp_path):
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        created = now - timedelta(hours=200)
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "TEST_FAILURES.md", created, ttl_hours=168)
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert "TTL expired" in result
        assert "ttl=168" in result

    def test_short_custom_ttl_expires(self, tmp_path):
        """A 1h TTL file that is 2 hours old should be expired."""
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        created = now - timedelta(hours=2)
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "DESIGN_QUESTIONS.md", created, ttl_hours=1)
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert "TTL expired" in result


# ---------------------------------------------------------------------------
# Orphan detection tests
# ---------------------------------------------------------------------------

class TestOrphanDetection:
    def test_unknown_event_id_is_orphan(self, tmp_path):
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "REVIEW_FAILURES.md", now, event_id="evt-GONE")
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001", "evt-002"})

        assert "orphan" in result

    def test_known_event_id_is_not_orphan(self, tmp_path):
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "REVIEW_FAILURES.md", now, event_id="evt-123")
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-123", "evt-456"})

        assert result == ""

    def test_empty_known_event_ids_skips_orphan_check(self, tmp_path):
        """If EVENTS.jsonl is empty/missing, don't flag everything as orphan."""
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "ARCH_FEEDBACK.md", now, event_id="evt-001")
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids=set())  # empty set

        assert result == ""

    def test_event_id_unknown_literal_skips_orphan_check(self, tmp_path):
        """created_by_event: unknown should not trigger orphan detection."""
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        f = _write_feedback(fb_dir, "IMPL_QUESTIONS.md", now, event_id="unknown")
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert result == ""


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_file_without_frontmatter_is_ignored(self, tmp_path):
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        fb_dir.mkdir(parents=True, exist_ok=True)
        f = fb_dir / "REVIEW_FAILURES.md"
        f.write_text("No frontmatter here.\n", encoding="utf-8")
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert result == ""

    def test_missing_created_at_skips_ttl_check(self, tmp_path):
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        fb_dir.mkdir(parents=True, exist_ok=True)
        f = fb_dir / "TEST_FAILURES.md"
        f.write_text("---\ncreated_by_event: evt-001\nttl_hours: 1\n---\nContent.\n", encoding="utf-8")
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert result == ""

    def test_nonexistent_file_returns_empty(self, tmp_path):
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        files = _make_files(tmp_path, _fixed_clock(now))
        ghost = tmp_path / "plans" / "test-feature" / "feedback" / "GHOST.md"

        result = files.feedback_ttl_issue(ghost, known_event_ids={"evt-001"})

        assert result == ""

    def test_default_ttl_is_168_hours(self, tmp_path):
        """Verify the default TTL is 1 week (168h), not 24h."""
        now = datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc)
        # 100 hours ago — would expire under old 24h default but not under 168h
        created = now - timedelta(hours=100)
        fb_dir = tmp_path / "plans" / "test-feature" / "feedback"
        fb_dir.mkdir(parents=True, exist_ok=True)
        f = fb_dir / "REVIEW_FAILURES.md"
        # Write frontmatter WITHOUT ttl_hours so the default kicks in
        content = (
            f"---\n"
            f"created_at: {created.isoformat()}\n"
            f"created_by_event: evt-001\n"
            f"---\n"
            f"Content.\n"
        )
        f.write_text(content, encoding="utf-8")
        files = _make_files(tmp_path, _fixed_clock(now))

        result = files.feedback_ttl_issue(f, known_event_ids={"evt-001"})

        assert result == "", (
            "Default TTL should be 168h (1 week). "
            "A 100h-old file should NOT be expired. Got: " + result
        )
