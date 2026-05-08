# installable-workflow-architecture - User Stories

## Context

Pathly already has the right product core: files are the protocol, role
contracts define agent behavior, and the orchestrator is a deterministic
filesystem state machine. The next implementation increment should make that
core usable from an installed package without requiring users to clone this
repository or manually wire host-specific adapter files.

This plan turns the installable workflow architecture proposal into scoped
builder conversations. The implementation order intentionally proves package
resources and clean install behavior before adding mutating setup commands.
Pathly remains a public beta candidate until clean-machine install, adapter,
hook, and host smoke gates are verified.

## Stories

### Story S1.1: Package assets load from an installed package
**As a** Pathly maintainer, **I want** core prompts, role contracts, templates,
and adapter assets loaded through a package resource API, **so that** Pathly can
run outside the source checkout.

**Acceptance Criteria:**
- [ ] Pathly exposes a host-neutral resource API for core prompts, templates,
      role contracts, and adapter assets.
- [ ] CLI and installer code no longer depends on repo-root `core/` or
      `adapters/` paths for packaged assets.
- [ ] Packaging tests prove required assets are present in the built artifact.
- [ ] `pathly --version` reports the installed package version.

**Edge Cases:**
- Package is installed in a virtual environment.
- Commands run from a non-Pathly project directory.
- Required packaged assets are missing or malformed.

**Delivered by:** Phase 1 -> Conversation 1

### Story S1.2: Clean install smoke works outside the source checkout
**As a** new user, **I want** `pip install pathly` to expose a working CLI, **so
that** I can start using Pathly without cloning the repo.

**Acceptance Criteria:**
- [ ] A wheel can be built and installed into a fresh virtual environment.
- [ ] The installed `pathly` command runs `--version`, `--help`, `doctor`, and
      `help` from a temporary non-Pathly directory.
- [ ] Diagnostics distinguish missing host tools from Pathly install failures.
- [ ] No smoke command requires `C:\Users\Yafit\pathly` or another checkout path.

**Edge Cases:**
- Claude Code is not installed.
- Codex is not installed.
- A project has no `plans/` directory yet.

**Delivered by:** Phase 2 -> Conversation 1

### Story S2.1: Setup reports before it mutates
**As a** user, **I want** `pathly setup` and host-specific dry runs to show
detected hosts and planned writes, **so that** I can review changes before
Pathly modifies files.

**Acceptance Criteria:**
- [ ] `pathly setup` defaults to a safe report.
- [ ] `pathly setup --dry-run`, `pathly setup claude --dry-run`, and
      `pathly setup codex --dry-run` write no files.
- [ ] Setup output shows detected hosts, Pathly version, planned adapter
      writes, planned hook registration, conflicts, and final start commands.
- [ ] Unsupported or missing hosts produce useful next steps.

**Edge Cases:**
- Multiple supported hosts are installed.
- No supported host is installed.
- Existing adapter files are present from an older Pathly install.

**Delivered by:** Phase 3 -> Conversation 2

### Story S2.2: Setup materializes adapters safely
**As a** user, **I want** setup apply, repair, and force behavior to install
Pathly adapters from packaged resources, **so that** Claude Code and Codex can
use Pathly without manual wiring.

**Acceptance Criteria:**
- [ ] Adapter files are copied from packaged resources into approved user-level
      Pathly data locations.
- [ ] User data adapter snapshots are versioned by Pathly version.
- [ ] Existing non-Pathly files are not overwritten unless `--force` is used.
- [ ] `--repair` refreshes stale Pathly-owned files.
- [ ] Codex guidance remains natural language, not `/pathly` slash commands.

**Edge Cases:**
- User data directory is missing.
- User data directory contains stale Pathly-owned files.
- User data directory contains unrelated files.

**Delivered by:** Phase 4 -> Conversation 2

### Story S3.1: Status and doctor explain recovery
**As an** interrupted workflow user, **I want** `pathly status` and improved
`pathly doctor` output, **so that** I know the next safe action without reading
raw FSM internals.

**Acceptance Criteria:**
- [ ] `pathly status [feature]` summarizes active feature state, open feedback,
      next owner, and suggested next command.
- [ ] `doctor` distinguishes install problems, adapter problems, hook problems,
      and workflow state problems.
- [ ] Missing state, feedback-blocked state, done state, and adapter-broken
      state each have distinct output.
- [ ] Suggested actions are real CLI or host commands.

**Edge Cases:**
- `STATE.json` is missing but plan files exist.
- `EVENTS.jsonl` disagrees with feedback files.
- Multiple feedback files are open at the same time.

**Delivered by:** Phase 5 -> Conversation 3

### Story S3.2: Hooks stay bounded guardrails
**As a** maintainer, **I want** hooks to validate paths, classify feedback, add
metadata, and emit diagnostics only, **so that** hooks do not secretly drive the
workflow.

**Acceptance Criteria:**
- [ ] Hook payload paths are canonicalized and constrained to the active
      project.
- [ ] Hook writes stay under the active project `plans/` tree.
- [ ] Malformed payloads and unsupported hosts produce visible diagnostics.
- [ ] Hooks never spawn lifecycle agents, edit source code, or advance FSM
      lifecycle state.

**Edge Cases:**
- Hook payload is malformed JSON.
- Hook target path attempts traversal outside the project.
- Hook host does not support a documented native schema.

**Delivered by:** Phase 6 -> Conversation 3

### Story S4.1: Host smoke and docs match verified behavior
**As a** Pathly adopter, **I want** docs and setup output to match verified
Claude Code, Codex, CLI, and hook behavior, **so that** onboarding instructions
are trustworthy.

**Acceptance Criteria:**
- [ ] CLI smoke covers `pathly go`, `pathly help`, `pathly doctor`, and
      installed package startup.
- [ ] Claude Code smoke covers `/pathly help` and `/pathly add password reset`
      when the host is available.
- [ ] Codex smoke covers `Use Pathly help` and `Use Pathly to add password
      reset` when the host is available.
- [ ] README/docs only claim behavior that the smoke matrix verifies.
- [ ] Public release language remains "public beta candidate", not
      production-ready.

**Edge Cases:**
- A host is not installed on the verification machine.
- A host plugin is installed but disabled.
- Manual smoke cannot be completed in the current environment.

**Delivered by:** Phase 7 -> Conversation 4
