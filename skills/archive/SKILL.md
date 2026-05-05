---
name: archive
description: Archive a completed feature plan by moving plans/<feature>/ to plans/.archive/<feature>/. Requires RETRO.md to exist and all conversations to be DONE. Recoverable via git.
argument-hint: "<feature-name>"
model: haiku
---

## Pathly Command Surface

Use `/pathly <command>` as the canonical cross-framework command form. `/path <command>` is the short alias. Legacy direct skill commands may remain available in some hosts for backwards compatibility, but user-facing guidance should prefer `/pathly` or `/path`.

## Step 1: Validate

If `$ARGUMENTS` is empty: stop →
```
Usage: /pathly archive <feature-name>
Example: /pathly archive hotel-search
```

Set `FEATURE = $ARGUMENTS`.

Check `plans/$FEATURE/` exists. If not: stop →
```
plans/$FEATURE/ not found. Nothing to archive.
```

Check `plans/$FEATURE/RETRO.md` exists. If not: stop →
```
RETRO.md missing. Run /pathly retro $FEATURE before archiving.
The retro seed is needed for future storm sessions.
```

Read `plans/$FEATURE/PROGRESS.md`. Check all conversations are DONE.
If any TODO: stop →
```
$FEATURE has incomplete conversations. Finish building before archiving.
Incomplete: [list the TODO conversations]
```

Check `plans/$FEATURE/feedback/` — any open feedback files? If yes: stop →
```
Open feedback files found: [list them]
Resolve all feedback before archiving.
```

---

## Step 2: Archive

Create `plans/.archive/` if it does not exist.

Move `plans/$FEATURE/` → `plans/.archive/$FEATURE/`

Use the Bash tool:
```bash
mv plans/$FEATURE plans/.archive/$FEATURE
```

---

## Step 3: Report

```
Archived: $FEATURE

  From: plans/$FEATURE/
  To:   plans/.archive/$FEATURE/

  Recoverable: git checkout plans/$FEATURE/
  RETRO.md seed: plans/.archive/$FEATURE/RETRO.md

plans/ is now clean.
```

If `plans/` now has no remaining active features, add:
```
No active features remaining. Start the next one with:
  /pathly flow <new-feature>
```
