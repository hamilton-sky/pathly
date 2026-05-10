# pathly-interface-redesign — Happy Flow

## Scenario A: Starting a new feature (first time user)

1. User opens their AI coding tool (Claude Code, Codex, or Copilot)
2. User types: `/pathly start`
3. Skill reads STATE.json — no active feature found
4. Skill routes to director with no arguments
5. Director responds: "What do you want to build?"
6. User types: "I want to add user authentication"
7. Director infers feature name (`user-authentication`), selects `lite` rigor
8. Director spawns orchestrator with feature context
9. Orchestrator creates `plans/user-authentication/STATE.json`
10. Pipeline begins normally

## Scenario B: Resuming work after a break

1. User returns to their tool the next day
2. User types: `/pathly continue`
3. Skill reads `plans/` — finds `user-authentication` with STATE.json modified most recently
4. Skill routes directly to orchestrator (no director needed)
5. Orchestrator reads STATE.json: state is `BUILDING`, Conv 2 is next
6. Orchestrator prints: `[FSM] State recovered from STATE.json: BUILDING`
7. Builder is spawned for Conv 2 — work resumes

## Scenario C: Mid-flow consultation with architect

1. User is in the middle of a build flow and has a design question
2. User types: `/pathly meet`
3. Skill reads STATE.json — active feature is `user-authentication`, state is `BUILDING`
4. Skill shows role menu filtered to building state: planner, architect, reviewer, tester, scout
5. User picks `[2] architect`
6. Skill asks: "What is the one question you want to ask the architect?"
7. User asks: "Should we use JWT or session cookies?"
8. Architect reads plan files, answers the question
9. Consult note written to `plans/user-authentication/consults/20260510-143022-architect.md`
10. Menu shown: [1] Return to build [2] Promote to architecture update [3] Ask another
11. User picks [1] — returns to build flow

## Scenario D: Closing a completed feature

1. All conversations are done, user wants to wrap up
2. User types: `/pathly end`
3. Skill reads STATE.json — state is `BUILD_DONE` or `TESTING`
4. Orchestrator confirms: "All conversations complete. Proceed to retro? [yes/no]"
5. User types: yes
6. Retro agent runs, writes `plans/user-authentication/RETRO.md`
7. Skill prints: "Feature 'user-authentication' is DONE. Use `/pathly help` to start next feature."

## Scenario E: Developer installs Pathly fresh

1. Developer runs `pip install pathly`
2. Developer runs `pathly install` (or `pathly install --dry-run` to preview)
3. Installer reads all `core/agents/*.md` files
4. Installer reads all `adapters/claude/_meta/*.yaml` files
5. Installer stitches each pair: frontmatter + core body + spawn section
6. Installer writes stitched files to `~/.claude/agents/`
7. Installer reports: "11 agents stitched → ~/.claude/agents/"
8. Developer opens Claude Code — all Pathly agents available immediately
