# Core Agents

Tool-agnostic behavioral contracts for Pathly roles belong here.

Each agent file should describe:

- role
- responsibility boundaries
- inputs it reads
- files it may write
- handoff rules
- failure and escalation behavior

Do not include Claude Code frontmatter, Codex plugin fields, or tool-specific
model names in these core files. Adapters add that metadata.
