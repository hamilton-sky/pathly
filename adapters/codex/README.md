# Codex Adapter

Codex should expose Pathly through one namespaced entry point:

```text
/pathly ...
```

This avoids collisions with Codex built-ins such as `/help`.

Recommended commands:

```text
/pathly help
/pathly doctor
/pathly add password reset
/pathly debug checkout button does nothing
/pathly explore how auth state flows
/pathly flow checkout-flow
```

Current status: the live Codex plugin still reads `skills/` from the repository
root. The working `/pathly` router lives at `skills/pathly/SKILL.md` until the
adapter generator exists.
