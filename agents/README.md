# Agents

Agents are architectural roles with behavioral contracts. A role defines how the
agent thinks. Skills are the abilities that role can execute.

## Role Map

| Agent | Role | Model | Skills | Invoke when |
|---|---|---|---|---|
| `director` | director | sonnet | go, team-flow, build, review, retro | Natural-language entry point; chooses workflow, rigor, and entry stage |
| `architect` | architect | opus | storm | Technical design, layer decisions, trade-offs, system design |
| `po` | po | opus | — | Interactive requirements discussion; probes scope, challenges assumptions, validates PRDs |
| `planner` | product-owner | sonnet | storm, plan | Requirements, user stories, conversation decomposition, plans/ folder |
| `builder` | executor | sonnet | build | Coding, verification, staying in scope |
| `tester` | tester | sonnet | test | Verifying acceptance criteria, test plans, coverage gaps |
| `quick` | analyst | haiku | retro | Fast lookups, short summaries, focused tasks (≤2 tool calls) |
| `reviewer` | reviewer | sonnet | review, verify-layers, security-review | Adversarial review, contract violations, security |
| `discoverer` | discoverer | sonnet | discover-site, generate-poms | Navigating live sites, tracing user journeys, POM generation |
| `orchestrator` | orchestrator | haiku | team-flow | Recovering FSM state and running the full pipeline |
| `scout` | analyst | haiku | — | Read-only codebase investigation; spawned by builder/reviewer/tester/architect |
| `web-researcher` | analyst | haiku | — | Read-only web research; spawned by architect/planner for external docs and patterns |

## Architecture

```text
User request
  -> director
       decides intent, risk, rigor, and entry point
       invokes /go, /team-flow, /review, /build, or /retro
  -> orchestrator
       recovers filesystem FSM state
       routes one next action
  -> architect / planner / builder / reviewer / tester / quick
```

Director sits above the orchestrator. Director makes product/process decisions:
whether the task is `nano`, `lite`, `standard`, or `strict`; whether to storm,
probe, plan, build, test, review, or stop for clarification.

Orchestrator stays deterministic. It owns filesystem state recovery, event logs,
feedback routing, retry limits, and stage transitions.

## Handoff Contract

```text
director
  -> chooses workflow and invokes /team-flow

orchestrator
  -> runs the filesystem FSM

storm (architect)
  -> STORM_SEED.md

plan (planner)
  -> plans/<feature>/
       USER_STORIES.md
       IMPLEMENTATION_PLAN.md
       CONVERSATION_PROMPTS.md
       PROGRESS.md
       optional rigor-specific extras

build (builder) x N
  -> implementation changes
  -> PROGRESS.md updates

review (reviewer)
  -> PASS or feedback files

test (tester)
  -> acceptance criteria verification

retro (quick)
  -> RETRO.md
```

## Entry Point

Prefer the natural-language front door:

```text
/go <what you want>
```

Direct pipeline entry is still available:

```text
/team-flow <feature-name>
/team-flow <feature-name> fast
/team-flow <feature-name> nano
/team-flow <feature-name> lite
/team-flow <feature-name> standard
/team-flow <feature-name> strict
```

## For Teams

Each role is a clear ownership boundary:

- **director** owns what workflow should run for the user's request.
- **architect** owns how things should be built technically.
- **planner** owns what should be built and for whom.
- **builder** owns building what was planned.
- **tester** owns verifying what was built matches what was planned.
- **analyst** owns learning and reporting fast.
- **reviewer** owns finding what is wrong before it ships.
- **discoverer** owns understanding a site or code path before implementation.
- **orchestrator** owns deterministic workflow state and feedback routing.
