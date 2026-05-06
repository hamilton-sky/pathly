# meet

This is the canonical, tool-agnostic Pathly behavior for the meet workflow.
Adapter skills should load and follow this prompt instead of duplicating workflow logic.

## Purpose

`meet` is an advanced, read-only consultation workflow.

Use it when the user wants to ask one named role a bounded question during an
existing feature flow without editing code or silently changing pipeline state.

The consulted role gives advice only. It does not resolve feedback files, does
not update source code, and does not change workflow state on its own.

## Step 1: Detect context

1. Infer `FEATURE` from `$ARGUMENTS` if provided.
2. If `$ARGUMENTS` does not name a feature, scan `plans/` and use the most
   recently modified active feature folder.
3. Read these files when present:
   - `plans/$FEATURE/PROGRESS.md`
   - `plans/$FEATURE/feedback/`
   - `plans/$FEATURE/STATE.json`
   - `plans/$FEATURE/EVENTS.jsonl`
4. Infer the current workflow state in plain language:
   - planning
   - building
   - review feedback open
   - architecture feedback open
   - testing
   - done / retro complete

If no active feature exists, say:

```text
meet requires an active feature plan. Start a feature first, then run meet again.
```

Stop there.

## Step 2: List relevant roles

Offer only the roles relevant to the current state.

Default role sets:

- **planning** -> `planner`, `po`, `architect`
- **building** -> `planner`, `architect`, `reviewer`, `tester`, `scout`
- **review feedback open** -> `reviewer`, `architect`, `planner`, `scout`
- **architecture feedback open** -> `architect`, `planner`, `reviewer`, `scout`
- **testing** -> `tester`, `planner`, `architect`, `reviewer`, `scout`
- **done / retro complete** -> `reviewer`, `tester`, `planner`

Rules:

- Do not offer `builder` as a meet target. Builder is an implementation owner,
  not an advisory role.
- Do not offer `director` as a meet target. Director routes workflows; it does
  not act as a subject-matter consultant.
- Offer `po` only when product intent, scope, user value, or success criteria
  are plausible consultation topics.
- Offer `web-researcher` only if the user explicitly wants external references.

Print the menu in this format:

```text
===========================================
  meet - <feature>
  State: <state>
===========================================

  Pick a role to consult:

  [1] planner      -> requirements, stories, acceptance criteria, task breakdown
  [2] architect    -> design, layers, contracts, migrations, rollback
  [3] reviewer     -> likely review risks, contract violations, diff quality
  [4] tester       -> verification strategy, acceptance coverage, likely gaps
  [5] scout        -> read-only codebase investigation
  [6] See all commands

Reply with 1-6:
```

## Step 3: Collect one bounded question

After the user picks a role, ask:

```text
What is the one question you want to ask <role>?
```

Rules:

- Keep the consultation to one bounded question.
- If the user asks multiple unrelated questions, ask them to choose one first.
- If the question implies code changes, redirect the role to advice only.

## Step 4: Run the consultation

Invoke the selected role in read-only mode.

Consultation rules for every role:

- Read project files as needed.
- May spawn only read-only subagents allowed by that role.
- Must not edit code.
- Must not edit plan files.
- Must not delete feedback files.
- Must not claim the workflow has advanced.
- Must answer the user's question directly and concretely.

Write the consultation note to:

`plans/$FEATURE/consults/YYYYMMDD-HHMMSS-<role>.md`

Use this structure:

```markdown
# Meet Note - <role> - <feature>

## Question
+[the bounded user question]

## Answer
+[direct answer]

## Evidence
- [files read, patterns found, or external sources if web-researcher was used]

## Recommendation
+[what the user should do next]

## Promotion Target
- none
- planner
- architect
```

Promotion target rules:

- `planner` if the answer should change stories, acceptance criteria, ordering,
  or decomposition.
- `architect` if the answer should change design, contracts, layers, rollback,
  or integration shape.
- `none` if the answer is advisory only.

## Step 5: Print next choices

After writing the consult note, print:

```text
Meet note written: plans/<feature>/consults/<timestamp>-<role>.md

What do you want to do next?

[1] Return to build
[2] Promote to planner update
[3] Promote to architecture update
[4] Ask another meet question
[5] See all commands

Reply with 1-5:
```

Interpret the choices as:

- **Return to build** -> route back to `team-flow <feature> build`
- **Promote to planner update** -> planner reads the consult note and updates
  plan files if warranted
- **Promote to architecture update** -> architect reads the consult note and
  updates architecture docs if warranted
- **Ask another meet question** -> restart `meet <feature>`
- **See all commands** -> print the help command reference

If the current state is not building, adapt the first option label to the most
natural return route, such as `Return to test` or `Return to review resolution`.

## Step 6: Promotion behavior

If the user chooses planner or architect promotion:

- Read the consult note.
- Update only the plan or architecture files that are directly affected.
- Report exactly what changed.
- Do not change source code.
- After the update, offer the same return options again.
