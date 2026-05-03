# Philosophy — Why This System Is Built the Way It Is

*The five convictions behind the Claude Agents Framework.*

---

## 1. Files are the protocol, not function calls

Most multi-agent systems pass messages between agents — direct calls, shared queues, in-memory state. This system does not. Every agent writes a file when its job is done. The next agent reads that file. Nothing else.

This means:

- **Any agent can stop and resume** because the file is always there.
- **State is inspectable** — open `plans/<feature>/` and you know exactly where things stand.
- **Agents are replaceable** — swap the builder, the planner still reads the same plan files.

The file is not a side effect of the process. It *is* the process.

---

## 2. Agent = behavioral contract, not persona

Most agent frameworks define agents as characters: "You are a helpful assistant who specializes in..." This system defines agents as constraints: here is what you think about, here is what you must never do.

The difference is load-bearing.

A persona drifts. Given enough turns, a "senior architect" starts writing code, a "reviewer" starts fixing things instead of reporting them. A behavioral contract does not drift — the rules are structural, not stylistic.

```
reviewer.md:
  "Find what's wrong before it ships."
  "Adversarial. Reports violations with file + rule reference. Never edits."
```

That is not a personality. It is a constraint. The role is stable across every project.

---

## 3. Feedback loops, not a linear chain

A naive pipeline is a straight line: Storm → Plan → Build → Test → Done. When the tester finds a problem that originated in the plan, a straight line has no path back. You stop, or you ignore it.

This system routes problems to their exact owner through typed feedback files:

```
reviewer finds architectural flaw  → ARCH_FEEDBACK.md    → architect redesigns
reviewer finds implementation bug  → REVIEW_FAILURES.md  → builder fixes
builder has requirement ambiguity  → IMPL_QUESTIONS.md   → planner clarifies
builder has technical blocker      → DESIGN_QUESTIONS.md → architect resolves
tester finds failing criterion     → TEST_FAILURES.md    → builder fixes
```

Not "broadcast an error." Not "go back to start." Each problem travels back to the specific role that owns it. The pipeline bends back and heals without breaking.

**File present = issue open. Deleted = resolved.** The orchestrator never advances past an open feedback file.

---

## 4. Human checkpoints are the point

The pipeline pauses at every stage transition. This is not a limitation — it is the design.

AI agents fail in long chains. Wrong assumptions compound. An architectural decision made in stage 2 can render five conversations of implementation worthless by stage 3. Pausing is cheap. Catching a wrong assumption at the plan review costs minutes. Catching it after three builder conversations costs hours.

The fast mode (`/team-flow <feature> fast`) exists for when you are confident. The default is pauses, because the default assumption is that you are not yet confident.

---

## 5. The shape: narrow nodes, explicit joints, typed return paths

Every unit in this system does exactly one job. Not "roughly one job" — one job. The reviewer never fixes. The builder never makes architecture decisions. The orchestrator never implements. Narrow nodes are where bugs surface cleanly; fat nodes are where bugs hide.

The connections between units are named contracts — feedback files with specific formats, plan files with specific sections, behavioral rules written into each agent. You cannot pass something through without naming it, making it visible, making it checkable.

The return paths are precise. Not a loop back to the start. `ARCH_FEEDBACK` goes to the architect specifically. `IMPL_QUESTIONS` goes to the planner specifically. Problems travel to their exact owner along labeled paths.

```
 ┌──────────┐      ┌──────────┐      ┌──────────┐
 │ architect│─────►│ planner  │─────►│ builder  │
 └──────────┘      └──────────┘      └──────────┘
      ▲                  ▲                 │
      │ ARCH_FEEDBACK     │ IMPL_QUESTIONS  │
      │                   └────────────────┘
      └──────────────────────────────────────── from reviewer
```

One-way spine. Named joints. Typed return paths. **Clarity made structural.**

---

## 6. Memory that improves plans, not agents

The lessons system (`/retro` → `LESSONS_CANDIDATE.md` → `/lessons` → `LESSONS.md`) does not make agents smarter. It compresses repeated failures into enforced planning constraints.

When the same failure pattern appears in three different feature retros, it is promoted into `LESSONS.md` as an injection the planner applies before the next plan is written. The agent does not learn — the plan gets harder to fail.

This is the distinction:
- **Smarter agent** → unpredictable, harder to audit
- **Better constraint** → deterministic, reviewable, deletable

Lessons are constraints, not memory. They change what gets planned, not how the planner thinks.

---

## The through-line

Every design decision in this framework expresses the same answer to the same question:

> *How do you build a system where independent units collaborate reliably, failures are caught early, and no single unit carries too much responsibility?*

1. Give each unit exactly one job.
2. Make boundaries explicit and enforced — not advisory.
3. Route problems back to their owners through a structured protocol.
4. Catch things early, before the next stage begins.
5. Store state on disk so the system survives any interruption.
6. Let repeated failures tighten the plan, not complicate the agent.
