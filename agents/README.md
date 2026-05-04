# Agents

Agents are architectural roles with behavioral contracts.
A role defines HOW the agent thinks. Skills are the abilities that role can execute.

## Role Map

| Agent | Role | Model | Skills | Invoke when |
|---|---|---|---|---|
| `architect` | architect | opus | storm | technical design, layer decisions, trade-offs, system design |
| `planner` | product-owner | sonnet | storm, plan | requirements, user stories, conversation decomposition, plans/ folder |
| `builder` | executor | sonnet | build | coding, verification, staying in scope |
| `tester` | tester | sonnet | test | verifying acceptance criteria, test plans, coverage gaps |
| `quick` | analyst | haiku | retro | fast lookups, short summaries, focused tasks |
| `reviewer` | reviewer | sonnet | review, verify-layers, security-review | adversarial review, contract violations, security |
| `discoverer` | discoverer | sonnet | discover-site, generate-poms | navigating live sites, tracing user journeys, POM generation |
| `orchestrator` | orchestrator | haiku | team-flow | recovering FSM state and running the full pipeline — use `/team-flow <feature>` |

## Architecture

```
role: architect      (architect)
  behavior: technical HOW — layers, dependencies, design decisions
  skills:   storm ──────────────► explore technical ideas

role: product-owner  (planner)
  behavior: product WHAT — stories, criteria, decomposition
  skills:   storm ──────────────► explore product ideas
            plan ─────────────────► produce the plans/ folder

role: executor       (builder)
  behavior: stays in scope, verifies before done, no silent changes
  skills:   build ────────────────► implement one conversation

role: tester         (tester)
  behavior: verifies stories, reports bugs, never fixes
  skills:   test ────────────────► run tests + verify criteria

role: analyst        (quick)
  behavior: direct, 2 tool calls max, no preamble
  skills:   retro ───────────────► extract learnings

role: reviewer       (reviewer)
  behavior: adversarial, finds violations, never fixes
  skills:   review ──────────────► check against rules
            verify-layers ────────► audit layer contracts

role: discoverer     (discoverer)
  behavior: trace before generate, follow visible path
  skills:   discover-site ────────► navigate + capture trace
            generate-poms ──────────► build three-layer impl

role: orchestrator   (orchestrator)
  behavior: filesystem FSM, enforces pauses, emits one subagent action
  skills:   team-flow ────────────► full storm→retro pipeline
```

## Handoff contract (file-based)

```
storm (architect)
  └─► STORM_SEED.md
            │
            ▼
      plan (planner)
            └─► plans/<feature>/
                  ├─ USER_STORIES.md      (stories + acceptance criteria)
                  ├─ IMPLEMENTATION_PLAN.md (phases + story cross-refs)
                  ├─ CONVERSATION_PROMPTS.md (prompts + stories delivered)
                  ├─ PROGRESS.md          (story status + conv status)
                  └─ ...5 more files
                      │
                      ▼
              build (builder) × N
                      └─► PROGRESS.md (story: TODO→DONE per conv)
                                │
                                ▼
                          test (tester)
                                └─► acceptance criteria verified
                                          │
                                          ▼
                                    retro (quick)
                                          └─► RETRO.md
```

## Entry point

Start any feature with:
```
/team-flow <feature-name>        ← with human pause points
/team-flow <feature-name> auto   ← fully automated
```

## For teams

Each role is a clear ownership boundary:
- **architect** owns: how things should be built technically
- **planner** owns: what should be built and for whom
- **builder** owns: building what was planned
- **tester** owns: verifying what was built matches what was planned
- **analyst** owns: learning and reporting fast
- **reviewer** owns: finding what's wrong before it ships
- **discoverer** owns: understanding a site before implementing it

Invoke by role: "this needs architecture thinking" → use `architect` agent.
