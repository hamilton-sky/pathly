# AGENTS.md

Guidance for Codex and other coding agents working in this repository.

## Project

Pathly is a local agent workflow framework. It provides planning, build, review,
test, retrospective, and plugin/adapter workflows for agent-assisted software
delivery.

## Working Rules

- Prefer small, focused changes that match the existing code and docs.
- Read the relevant plan files before editing feature work under `plans/`.
- Treat docs, prompts, adapters, CLI behavior, and tests as one product surface.
- Do not rewrite unrelated files or revert user changes.
- Keep public-facing release language honest. Unless freshly verified otherwise,
  describe Pathly as a public beta candidate, not production-ready.
- When behavior changes, update the matching README/docs/prompts/tests if they
  would otherwise drift.
- When the user asks to fix issues, implement and verify the fix instead of only
  giving advice.
- When the user explicitly asks to commit and push after work, treat that as
  part of completion after verification.

## Pathly Workflow Conventions

- Keep `po` optional and on-demand; do not make it a default pipeline stage.
- Keep `architect` consultation on-demand and tied to real design uncertainty.
- Keep builder-side consultation constrained to specific questions and outputs.
- Keep `meet` as a read-only consultation workflow that writes consult notes but
  does not change source code.
- Do not include `director` as a default `meet` consultation target.
- Decompose implementation plans into small tasks with purpose, dependencies,
  what each task enables, and verification.

## Repo Guidance Files

- `.codex-plugin/` is for Codex plugin packaging, not project rules.
- `.claude/rules/`, when present in a target project, contains optional project
  conventions for Claude-style workflows.
- Do not create `.Codex/rules` for this repo unless there is a specific tool
  requirement.

## Verification

- Run focused tests for the area changed.
- For broader workflow, CLI, prompt, or packaging changes, run `pytest -q` when
  practical.
- If tests cannot be run, report that clearly with the reason.
