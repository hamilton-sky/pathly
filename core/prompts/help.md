# help - Pathly State Menu

Show Pathly-specific help based on current project state.

This is not the host tool's help command. Adapters should avoid command-name
conflicts by exposing this as a namespaced command where needed, such as
`/pathly help` in Codex.

## Behavior

1. Detect the current feature from arguments or the newest `plans/<feature>/`
   folder.
2. Read progress, feedback files, state files, and retro files.
3. Show the next safe actions for that state.
4. If `doctor` mode is requested, diagnose stale or broken Pathly state and
   suggest one fix at a time.

## Common States

- no feature
- plan ready
- feedback open
- build complete
- retro complete
- stuck or inconsistent state
