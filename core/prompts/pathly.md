# pathly - Universal Entry Point

`pathly` is the tool-agnostic front door for Pathly.

It accepts a short command or a plain-English request and routes to the lightest
safe workflow.

## Inputs

- Optional command word: `help`, `doctor`, `debug`, `explore`, `flow`, `run`,
  `continue`, `review`
- Optional free text request
- Current project files, especially `plans/`, `debugs/`, and git status

## Routing

Use this order:

1. `help` with no other request: show Pathly help, not host-tool help.
2. `doctor`: diagnose Pathly state, stale feedback, missing files, and local
   prerequisites.
3. `debug <symptom>`: route to the debug workflow.
4. `explore <question>`: route to the read-only exploration workflow.
5. `flow <feature>` or `run <feature>`: route to the team-flow workflow.
6. `review`: review current code changes.
7. Any other text: treat as a plain-English request and route through the
   director workflow.

## Examples

```text
pathly help
pathly doctor
pathly add password reset
pathly debug checkout button does nothing
pathly explore how auth state flows
pathly flow checkout-flow
pathly continue checkout-flow
```

## Adapter Notes

- Codex exposes this as `/pathly ...` to avoid conflicts with built-in `/help`.
- Claude Code may keep `/go`, `/help`, `/debug`, and `/explore` for backwards
  compatibility.
- CLI exposes this through `pathly ...` commands where practical.
