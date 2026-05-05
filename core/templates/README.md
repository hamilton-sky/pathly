# Core Templates

Tool-agnostic plan, debug, feedback, and retro templates belong here.

`core/templates/` is the canonical template source. Adapter and runtime install
surfaces may copy these files into host-specific locations, but workflow prompts
should refer back to these core templates first.

Current template sets:

- `plan/`: Pathly plan files used by planning and import workflows.

The repo-root `templates/` folder remains as a compatibility/install surface for
current packaging.
