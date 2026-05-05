# Codex Adapter

Codex should expose Pathly through one namespaced entry point plus one short
alias:

```text
/pathly ...
/path ...
```

`/pathly` is canonical. `/path` is equivalent for daily use. Both avoid
collisions with Codex built-ins such as `/help`.

Recommended commands:

```text
/pathly help
/path help
/pathly doctor
/pathly add password reset
/pathly debug checkout button does nothing
/pathly explore how auth state flows
/pathly flow checkout-flow
```

Current status: the live Codex plugin still reads `skills/` from the repository
root. The working `/pathly` router lives at `skills/pathly/SKILL.md`, and the
short `/path` alias lives at `skills/path/SKILL.md`, until the adapter generator
exists.
