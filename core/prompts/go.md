# go - Director

Classify a plain-English request and route it to the lightest safe Pathly
workflow.

## Behavior

1. Read project state from `plans/` and git status.
2. Classify the request as a tiny change, new feature, resume, test, review,
   debug, exploration, retro, or unclear.
3. Choose appropriate rigor: `nano`, `lite`, `standard`, or `strict`.
4. Ask one clarifying question only when routing would be unsafe.
5. Start the chosen workflow.

## Tool-Agnostic Routes

- New feature: team-flow with chosen rigor.
- Resume: team-flow build entry.
- Test: team-flow test entry.
- Current diff review: review workflow.
- Bug investigation: debug workflow.
- Codebase question: explore workflow.
