# end

This is the canonical, tool-agnostic Pathly behavior for the end workflow.
Adapter skills should load and follow this prompt instead of duplicating workflow logic.

## Adapter Surface

This core prompt names Pathly workflows. Adapters translate those routes into their native surface.

The orchestrator owns FSM state. You are executing the session wrap-up flow — read disk state, summarize, and offer a clean exit. Do not modify PROGRESS.md or other state files except by invoking the documented routes.

---

## Step 1 — Check for in-progress feature

Scan `plans/` (skip `.archive/`). For each feature folder, read `PROGRESS.md` if present.

- Count conversations: DONE vs total.
- Identify any feature whose status is IN PROGRESS (has at least one TODO conversation).

---

## Step 2 — Report and offer retro

**If an in-progress feature is found:**

Print:

```
═══════════════════════════════════════════
  Session complete — <feature>
  Conversations: X done · Y remaining
═══════════════════════════════════════════

Write a retro? [y/n]
```

- **y** → invoke `retro <feature>`
- **n** → print `All done. Remember to commit your changes.` and stop

**If no in-progress feature is found:**

Print:

```
Nothing in progress. All done.
```

Stop.
