# [Feature Name] — Architecture Proposal

## Problem Statement
[What automation gap or framework capability are we adding?]

## Proposed Solution
[High-level description — new site, new action type, new resolver strategy, etc.]

## Three-Layer Breakdown

```
Flow layer   (plans/$ARGUMENTS — JSON workflow)
     │  "action": "xx_action_name"
     ▼
Glue layer   (stepper/sites/<site>/pages/<action>.py)
     │  _build_pom(SomePage, …, page=page, resolver=resolver)
     ▼
POM layer    (poms/<site>/pages/<page>.py)
     │  _resolve_and_click_any(BUTTON_CFG)
     ▼
ElementResolver cascade → Playwright
```

## Key Design Decisions

### Decision 1: [Title]
- **Options considered**: A, B, C
- **Chosen**: A
- **Rationale**: [Why A wins — e.g., label resolver is more resilient than CSS]

### Decision 2: [Title]
...

## New Action Names
[List action names that will be registered — must match workflow JSON "action" keys]

## cfg List Design
[For each interactive element: which resolver keys, in what priority order, and why]

## Risks
- [Risk 1]: [Mitigation — e.g., site uses dynamic IDs → use role + label resolvers first]
- [Risk 2]: [Mitigation]
