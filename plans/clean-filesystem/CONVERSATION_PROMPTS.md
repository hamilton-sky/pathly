# clean-filesystem - Conversation Guide

Split into 4 conversations. Each conversation must leave the codebase runnable
and end with verification. After each conversation, commit your changes before
starting the next if the user requested commit flow.

---

## Conversation 1: Stabilize package entrypoints (Phase 1)

**Stories delivered:** S1.1
**Depends on:** Baseline `pytest -q` is green before starting.

**Prompt to use:**
```text
Implement clean-filesystem Conversation 1 from
plans/clean-filesystem/IMPLEMENTATION_PLAN.md.

Stories delivered: S1.1.

Scope:
- Stabilize `pathly/cli/` as the canonical CLI package.
- Ensure `pathly/cli/__init__.py` exports `main`.
- Ensure `pathly/cli/__main__.py` supports `python -m pathly.cli --help`.
- Stabilize `pathly/team_flow/` as the canonical team-flow package.
- Ensure `pathly/team_flow/__init__.py` and `pathly/team_flow/__main__.py`
  support package-level imports and `python -m pathly.team_flow --help`.
- Update tests away from `scripts.team_flow` imports where needed.
- Confirm `pyproject.toml` keeps the console script pointed at the canonical CLI.

Do NOT touch runner abstraction, hook migration, legacy file deletion, or
packaging asset changes yet.

Verify:
- `python -m pathly.cli --help`
- `python -m pathly.team_flow --help`
- `pathly --help`
- `pytest -q`

After done, update `plans/clean-filesystem/PROGRESS.md` Conv 1 and Phase 1 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** Canonical package entrypoints work locally and through the
console script; tests no longer depend on `scripts.team_flow` for team-flow
runtime behavior.
**Files touched:** `pathly/cli/`, `pathly/team_flow/`, `pyproject.toml`, tests.

---

## Conversation 2: Introduce runner interface (Phase 2)

**Stories delivered:** S2.1
**Depends on:** Conversation 1 is DONE.

**Prompt to use:**
```text
Implement clean-filesystem Conversation 2 from
plans/clean-filesystem/IMPLEMENTATION_PLAN.md.

Stories delivered: S2.1.

Scope:
- Add `pathly/runners/base.py` with `RunnerResult`, `Runner`, shared errors,
  and timeout defaults.
- Add `pathly/runners/claude.py` preserving current Claude CLI command shape
  and usage parsing.
- Add `pathly/runners/codex.py` constructing `codex exec -C <repo> <prompt>`.
- Wire runtime selection for `--runner claude|codex|auto` and
  `PATHLY_RUNNER=claude|codex|auto`.
- Preserve Claude as the default behavior until Codex runner tests are green.
- Add focused tests for runner result shape, Claude compatibility, Codex command
  construction, and selection fallback.

Do NOT touch hook migration, legacy file deletion, packaging asset declarations,
or `.agents/skills/` handling yet.

Verify:
- `pytest -q`
- Optional when Codex CLI is available: `codex exec -C . "Use Pathly help"`

After done, update `plans/clean-filesystem/PROGRESS.md` Conv 2 and Phase 2 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** The FSM runtime depends on a host-neutral runner contract;
Claude remains compatible and Codex command construction is tested.
**Files touched:** `pathly/runners/`, runtime manager/driver files, tests.

---

## Conversation 3: Modularize hooks (Phase 3)

**Stories delivered:** S3.1
**Depends on:** Conversation 1 is DONE. Conversation 2 may be DONE but should not
be required for hook imports unless runner wiring already changed the same
runtime path.

**Prompt to use:**
```text
Implement clean-filesystem Conversation 3 from
plans/clean-filesystem/IMPLEMENTATION_PLAN.md.

Stories delivered: S3.1.

Scope:
- Create `pathly/hooks/contracts.py`.
- Move feedback-classification behavior into `pathly/hooks/classify_feedback.py`.
- Move feedback-TTL behavior into `pathly/hooks/inject_feedback_ttl.py`.
- Add CLI support for:
  - `pathly hooks run <event> --payload <json>`
  - `pathly hooks print-config claude`
  - `pathly hooks print-config codex`
  - `pathly hooks print-config cloud`
  - `pathly hooks install claude`
- Keep Claude hook config generated from the Python runtime.
- Add fixture-based tests for hook execution and config rendering.
- Treat Codex native hooks as unavailable unless a documented schema exists.

Do NOT delete root `hooks/`, shell hook setup scripts, bridge files, or
`.agents/skills/` yet.

Verify:
- `pathly hooks print-config claude`
- `pathly hooks run post-tool-use --payload <fixture-json>`
- `pytest -q`

After done, update `plans/clean-filesystem/PROGRESS.md` Conv 3 and Phase 3 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** Hook logic is importable from `pathly/hooks/`, host config can
be generated, and hook behavior is testable without root-level scripts.
**Files touched:** `pathly/hooks/`, CLI command files, tests.

---

## Conversation 4: Cleanup and packaging gate (Phases 4-5)

**Stories delivered:** S4.1, S1.2
**Depends on:** Conversations 1, 2, and 3 are DONE.

**Prompt to use:**
```text
Implement clean-filesystem Conversation 4 from
plans/clean-filesystem/IMPLEMENTATION_PLAN.md.

Stories delivered: S4.1 and S1.2.

Scope:
- Search for references before deleting each legacy path.
- Delete verified legacy files only after replacement checks pass:
  `pathly/cli.py`, `pathly/cli-2.py`, `pathly/team_flow.py`,
  `scripts/team_flow.py`, `scripts/team-flow-auto.sh`,
  `scripts/setup-hook.sh`, `scripts/setup-hook.ps1`, `scripts/__init__.py`,
  and root `hooks/`.
- Decide whether `.agents/skills/` is generated or committed for compatibility.
  If committed, add an exact-mirror verification against `adapters/codex/skills/`.
- Keep `examples/` at repo root.
- Update `pyproject.toml` package discovery and package-data declarations so
  built artifacts include runtime packages plus `core/` and `adapters/` assets.
- Add or update packaging tests that inspect artifact contents.
- Update install/packaging docs only if existing docs become inaccurate because
  of this cleanup.

Do NOT change FSM state semantics, public Pathly route names, or adapter skill
behavior beyond what is required for packaging and cleanup verification.

Verify:
- `rg "scripts.team_flow|pathly.cli-2|pathly/team_flow.py|setup-hook|hooks/" .`
- `pytest -q`
- `python -m build`
- Optional install gate: `pipx install --force dist\pathly-*.whl`
- Optional install gate: `pathly doctor`
- Optional install gate: `pathly install codex --apply --market C:\tmp\pathly-marketplace`

After done, update `plans/clean-filesystem/PROGRESS.md` Convs 4, Phase 4, and
Phase 5 to DONE.

If verification fails and the fix requires out-of-scope changes, stop and report.
If fundamentally broken, rollback with git checkout on affected files and retry.
```

**Expected output:** Legacy files are gone or explicitly justified, packaging
metadata is intentional, and build artifacts contain required runtime and asset
files.
**Files touched:** legacy runtime files, `scripts/`, root `hooks/`,
`.agents/skills/` if retained or generated, `pyproject.toml`, packaging tests,
install docs if needed.
