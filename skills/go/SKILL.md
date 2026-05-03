---
name: go
description: Natural language entry point — describe what you want in plain English and Claude routes you to the right skill automatically. No need to know /team-flow, /build, or /plan.
argument-hint: "<free text description of what you want>"
---

You are the entry point for the agent pipeline. The user described what they want in plain English via `$ARGUMENTS`. Your job is to read the project state, classify intent, confirm with the user, and invoke the right skill.

Never execute the work yourself. Route to the right skill and let it run.

---

## Step 1 — Read project state

Check the filesystem:

1. Does `plans/` exist and contain any feature folders?
2. For each folder in `plans/` (skip `.archive/`): read `PROGRESS.md` — count TODO vs DONE conversations.
3. Build a state map:
   ```
   feature          conversations    status
   ─────────────    ─────────────    ──────
   login            0/2 DONE         IN PROGRESS
   cart             2/2 DONE         COMPLETE
   ```

---

## Step 2 — Classify intent from `$ARGUMENTS`

Read the user's free text and classify into one of these intents:

| Intent | Signals | Route to |
|---|---|---|
| **new_feature** | "build", "add", "create", "implement", "I want", "make" | `/team-flow <name>` |
| **resume** | "continue", "resume", "finish", "keep going", "next step" | `/build <feature>` |
| **fix_or_review** | "fix", "broken", "something is wrong", "check", "review", "bug" | `/review` |
| **retro** | "retro", "wrap up", "done building", "retrospective" | `/retro <feature>` |
| **unclear** | anything else | show menu |

**Extracting the feature name for new_feature:**
- Strip filler words ("I want to", "build me a", "can you", "please")
- Kebab-case the result: "user login system" → `user-login`
- If user already has a matching folder in `plans/`, use that name

**Matching resume/retro to an existing feature:**
- If user mentions a name that matches a plans/ folder → use it
- If only one feature is IN PROGRESS → default to that
- If multiple IN PROGRESS → ask which one

---

## Step 3 — Confirm before routing

Print a confirmation block and wait for user reply. Do not skip this.

**For new_feature:**
```
Ready to start: [feature-name]

  Route: /team-flow [feature-name]
  This will: storm → plan → build → test → retro

Reply 'go' to start, or 'change [new-name]' to rename, or 'stop' to cancel.
```

**For resume:**
```
Resuming: [feature-name]
  [N/M conversations done]
  Next: Conversation [N+1]

  Route: /build [feature-name]

Reply 'go' to continue, or 'stop' to cancel.
```

**For fix_or_review:**
```
Running a code review on current staged changes.

  Route: /review

Reply 'go' to continue, or 'stop' to cancel.
```

**For unclear:**
```
Not sure what you need. Here's the current state:

[print state map from Step 1]

What would you like to do?
  [1] Start a new feature
  [2] Continue an in-progress feature
  [3] Review current code
  [4] Run a retro on a completed feature

Reply with a number, or describe what you want.
```

---

## Step 4 — Handle user reply

**On 'go':** invoke the routed skill immediately.

**On 'change [new-name]':** update feature name, re-print confirmation, wait again.

**On 'stop' or 'cancel':** print `Stopped. Run /go again whenever you're ready.` and exit.

**On a number (from unclear menu):**
- 1 → ask: `What's the feature called?` then route to `/team-flow <name>`
- 2 → if one IN PROGRESS: confirm + route to `/build <name>`. If multiple: list them, ask which.
- 3 → confirm + route to `/review`
- 4 → if one COMPLETE: confirm + route to `/retro <name>`. If multiple: list them, ask which.

---

## Step 5 — Invoke the skill

Run the routed skill exactly as you would if the user had typed it directly.
Pass the feature name and any inferred flags (do not add `fast` unless user asked for it).

Examples:
```
/team-flow user-login
/build cart
/review
/retro payment-flow
```
