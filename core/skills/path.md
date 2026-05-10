# path

This is the canonical, tool-agnostic Pathly behavior for the path workflow.
Adapter skills should load and follow this prompt instead of duplicating workflow logic.

# Path

Use this workflow as the short alias route for Pathly in adapters that support
aliases.

`path` is equivalent to `pathly`. Adapters may render this alias according to
their host.

## Route

Follow the same routing behavior as `core/skills/pathly.md`:

- `help`: run the Pathly help workflow.
- `doctor`: run Pathly doctor diagnostics.
- `debug <symptom>`: run the debug workflow.
- `explore <question>`: run the explore workflow.
- `flow <feature>` or `run <feature>`: run the team-flow workflow.
- `continue <feature>`: resume team-flow build for that feature.
- `review`: run the review workflow.
- any root skill name: run that skill with the remaining text as arguments.
- anything else: route through the director workflow as a plain-English request.

Before starting a route, print a one-sentence summary of the chosen action.
