# [Feature Name] — Flow Diagram

## [Primary Flow Name, e.g. "Happy Path: checkout workflow"]

```
[workflow JSON step]
        │  "action": "xx_step"
        ▼
[GlueAction._execute]
        │  _build_pom(Page, …, page=page, resolver=resolver)
        ▼
[POM method]
        │  _resolve_and_click_any(CFG_LIST)
        ▼
[ElementResolver cascade]
        │
        ├─ Phase 1: RoleResolver ──► unique match → click
        ├─ Phase 2: SemanticFilter (MiniLM)
        └─ Phase 3: AI Pick (Groq → Gemini → Claude)
```

## [Fallback / Error Flow]

```
[resolver finds 0 matches]
        │
        └─ raises ElementNotFoundError
                │
                └─ StepRunner catches → retry N times → fail step
```

## Component Legend

| Symbol | Meaning |
|--------|---------|
| [Name] | What this component does in this feature |
| ...    | ...                                       |
