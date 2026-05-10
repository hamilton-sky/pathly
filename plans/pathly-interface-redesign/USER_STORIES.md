# pathly-interface-redesign — User Stories

## Context

Pathly currently exposes skills that take arguments (`pathly flow <feature>`, `pathly continue <feature>`) and adapter agent files that duplicate behavioral content from `core/agents/`. This creates two problems: users must remember argument syntax per platform, and behavioral contracts drift when `core/agents/` is updated without syncing adapters.

This feature redesigns two layers: the skill surface (uniform no-argument verbs across all platforms) and the agent file architecture (thin adapter metas stitched at install time, no committed duplication).

## Stories

### S1.1: `/pathly start` — no-argument flow entry
**As a** user, **I want** to type `/pathly start` and have Pathly ask me what I want to build, **so that** I never need to remember CLI argument syntax.

**Acceptance Criteria:**
- [ ] `/pathly start` with no arguments prompts for intent and routes to the director
- [ ] Director infers feature name from conversation context or asks
- [ ] Works identically on Claude Code, Codex, and Copilot

**Edge Cases:**
- User types `/pathly start my-feature` — extra text treated as intent hint passed to director
- No `plans/` directory exists yet — start creates it during flow

**Delivered by:** Phase 1 → Conversation 1

---

### S1.2: `/pathly continue` — no-argument flow resume
**As a** user, **I want** to type `/pathly continue` and have Pathly resume my active flow, **so that** I don't need to remember the feature name between sessions.

**Acceptance Criteria:**
- [ ] `/pathly continue` reads `plans/` and finds the most recently active feature via STATE.json modification time
- [ ] If multiple active features exist, shows a numbered list to pick from
- [ ] Routes directly to orchestrator, not through director

**Edge Cases:**
- No active feature found — prints "No active flow. Use `/pathly start` to begin."
- STATE.json is corrupt or missing — falls back to PROGRESS.md scan

**Delivered by:** Phase 2 → Conversation 1

---

### S1.3: `/pathly end` — no-argument flow close
**As a** user, **I want** to type `/pathly end` to cleanly close the current flow and trigger a retrospective, **so that** I have a single command to finish work.

**Acceptance Criteria:**
- [ ] `/pathly end` detects active feature, confirms with user, then routes to retro
- [ ] If conversations are incomplete, warns and asks for confirmation before closing
- [ ] Retro note written to `plans/<feature>/RETRO.md`

**Edge Cases:**
- No active feature — prints "No active flow to end."
- All conversations already DONE — skips warning, goes straight to retro

**Delivered by:** Phase 3 → Conversation 1

---

### S2.1: `/pathly meet` — no-argument mid-flow consultation
**As a** user, **I want** to type `/pathly meet` during a flow and choose which expert to consult, **so that** I can get specialist advice without ending my flow.

**Acceptance Criteria:**
- [ ] `/pathly meet` detects active feature from STATE.json
- [ ] Shows a role menu filtered to what's relevant for the current flow state
- [ ] Consultation written to `plans/<feature>/consults/<timestamp>-<role>.md`
- [ ] After consultation, offers to return to flow or promote to planner/architect

**Edge Cases:**
- No active feature — prints contextual error
- User in retro-done state — shows limited role set (reviewer, tester, planner only)

**Delivered by:** Phase 4 → Conversation 1

---

### S2.2: `/pathly help` — context-aware state display
**As a** user, **I want** to type `/pathly help` and see options relevant to my current workflow state, **so that** I always know what to do next.

**Acceptance Criteria:**
- [ ] `/pathly help` scans STATE.json and prints a numbered menu matching current state
- [ ] Menu changes based on state: no-feature, plan-done, build-in-progress, feedback-open, build-done, retro-done
- [ ] All menu options use `/pathly [verb]` syntax, not platform-specific commands

**Edge Cases:**
- Unknown or corrupt state — shows full command reference
- Multiple active features — shows feature picker first

**Delivered by:** Phase 5 → Conversation 1

---

### S3.1: Agent meta YAML — thin adapter files
**As a** developer, **I want** adapter agent files to contain only frontmatter and spawn section, with behavioral content referenced from `core/agents/`, **so that** behavioral contracts have a single source of truth.

**Acceptance Criteria:**
- [ ] `adapters/{platform}/_meta/{agent}.yaml` exists for all agents on all platforms
- [ ] Each meta file contains: frontmatter fields (name, description, model, tools, can_spawn) + spawn_section block
- [ ] Adapter agent files in `adapters/{platform}/agents/` are removed or replaced by meta-only files
- [ ] `core/agents/{agent}.md` contains the complete behavioral contract with no spawn syntax

**Edge Cases:**
- Meta YAML is malformed — installer reports error with file + line
- `core/agents/{agent}.md` does not exist — installer skips and warns

**Delivered by:** Phase 1-2 → Conversation 2

---

### S3.2: Agent capability matrix — explicit `can_spawn`
**As a** developer, **I want** each agent's meta YAML to declare `can_spawn`, **so that** capability boundaries are explicit, enforceable, and visible in the installed agent file.

**Acceptance Criteria:**
- [ ] Every agent meta YAML has a `can_spawn` field listing permitted sub-agent types
- [ ] Terminal agents (quick, scout) have `can_spawn: []`
- [ ] The `can_spawn` list is injected into the stitched agent file as a section the agent can read
- [ ] Orchestrator has `can_spawn: all`

**Edge Cases:**
- Agent tries to spawn a type not in its `can_spawn` — the agent's own system prompt says not to (enforced by content, not by runtime)

**Delivered by:** Phase 3 → Conversation 2

---

### S4.1: Install-time stitching — no committed generated files
**As a** developer, **I want** `pathly install` to stitch `core/agents/{agent}.md` + `adapters/{platform}/_meta/{agent}.yaml` into the final agent file at install time, **so that** no generated files are committed to the repo.

**Acceptance Criteria:**
- [ ] `pathly install` reads each meta YAML, reads the matching core agent file, stitches them, writes to destination (`~/.claude/agents/`, `~/.codex/agents/`, etc.)
- [ ] `pathly install --dry-run` shows what would be written without writing
- [ ] Existing committed `adapters/{platform}/agents/*.md` files are replaced by a `_generated/` gitignored directory or removed entirely
- [ ] `pathly install` reports: agent name, source files stitched, destination written

**Edge Cases:**
- Destination directory does not exist — installer creates it
- Core agent file missing — installer skips that agent and warns, does not abort
- Meta YAML missing for an agent — installer skips and warns

**Delivered by:** Phase 1-2 → Conversation 3
