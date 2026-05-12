# engine-hardening — Edge Cases

## Conv 1 edge cases

**S1 — `is_available()` timeout:**
- CLI process starts but hangs indefinitely → `TimeoutExpired` caught → returns `False` (not a crash)
- CLI not installed → `FileNotFoundError` (existing behaviour, unchanged)
- CLI exits non-zero on `--version` → `CalledProcessError` (existing behaviour, unchanged)

**S2 — Path sanitization:**
- Feature name `../../.env` → `ValueError` before any filesystem access
- Feature name `foo/bar` → `ValueError`
- Feature name `foo\\bar` → `ValueError`
- Feature name `foo..bar` (contains `..` as substring) → `ValueError` — the check is `".." in name`, not a split
- Valid names like `my-feature`, `feature_123`, `pathly-server` → pass without error
- Empty string feature name → raise `ValueError` (empty name is also unsafe)

## Conv 2 edge cases

**S3 — Failure policy:**
- `required=True` agent exits 0 → normal flow (no change)
- `required=True` agent exits 1 → sys.exit(1) (existing behaviour, now documented)
- `required=False` agent exits 0 → normal flow (no change)
- `required=False` agent exits 1 → log warning + emit AgentDoneEvent + continue (now both tested and logged)
- `required=False` agent exits 0 but creates a feedback file → FSM blocks on feedback (unaffected by this change)

## Conv 3 edge cases

**S4 — E2E test:**
- Mock runner always returns exit 0; if runner returns non-zero in a future test variant, SystemExit should propagate from required agents
- `git init` in tmp_path may fail on CI if git is not installed → test should skip gracefully with `pytest.mark.skipif`
- PROGRESS.md with no TODO rows means BUILDING exits immediately; test patches `all_conversations_done` to return True to control this

## Conv 4 edge cases

**S5 — State-stack nesting:**
- If the reducer does NOT support FILE_CREATED(HUMAN_QUESTIONS) while already BLOCKED_ON_FEEDBACK (i.e., it ignores or errors), Conv 4 builder should stop and report rather than modify the reducer
- Emitting FILE_DELETED for a file not currently the `active_feedback_file` — verify reducer handles gracefully (no exception, state unchanged)
