# pathly-server — User Stories

**Feature:** pathly-server
**Delivered by:** Conv 1–5 (see IMPLEMENTATION_PLAN.md)

---

## S1 — Start dashboard with a single command

**As a** developer using Pathly,
**I want to** run `pathly server` and have a browser dashboard open automatically,
**so that** I can monitor and control the feature pipeline without memorising CLI commands.

### Acceptance criteria
- [ ] `pathly server` starts a FastAPI process on localhost:8765.
- [ ] The default browser opens to `http://localhost:8765` within 2 seconds of the server being ready.
- [ ] The server prints a ready message to stdout before opening the browser.
- [ ] `Ctrl+C` stops the server cleanly (no orphaned processes).
- [ ] If port 8765 is already in use, the command exits with a clear error message (not a stack trace).

### Edge cases
- Port already bound: fail fast with human-readable message.
- `plans/` directory does not exist yet: API returns an empty feature list, dashboard renders without crashing.

**Delivered by:** Conv 5 (S1)

---

## S2 — Kanban board shows pipeline stages

**As a** developer using Pathly,
**I want to** see a Kanban board with columns PLAN, BUILD, REVIEW, TEST, DONE,
**so that** I can tell at a glance which stage the active feature is in.

### Acceptance criteria
- [ ] The board renders five columns: PLAN, BUILD, REVIEW, TEST, DONE.
- [ ] The column matching `STATE.json → current` is visually highlighted (bold header or accent border).
- [ ] Completed stages have a check-mark indicator; future stages are visually dimmed.
- [ ] If no feature is active the board shows an empty-state message ("No active feature").

### Edge cases
- `STATE.json` is missing or malformed: board shows empty-state message, does not crash.
- `current` value is an unrecognised string: board highlights no column and logs a console warning.

**Delivered by:** Conv 3 (S2)

---

## S3 — Conversation cards with status

**As a** developer using Pathly,
**I want to** see each planned conversation as a card on the board with a TODO / IN_PROGRESS / DONE status,
**so that** I know exactly which conversation is running and which are pending.

### Acceptance criteria
- [ ] Each conversation listed in `STATE.json` (or derived from PROGRESS.md) appears as a card in the appropriate stage column.
- [ ] Cards display: conversation name/number, status icon (circle=TODO, spinner=IN_PROGRESS, check=DONE).
- [ ] At most one card is IN_PROGRESS at a time.
- [ ] Card statuses update when a new SSE event arrives (no manual refresh needed).

### Edge cases
- Zero conversations defined: column body is empty, no error.
- Conversation status outside known values: card renders with a neutral "unknown" icon.

**Delivered by:** Conv 3 (S3)

---

## S4 — Sidebar file list with inline markdown preview

**As a** developer using Pathly,
**I want to** click any MD file in the sidebar to see it rendered as a markdown card inline in the chat panel,
**so that** I can read the plan without leaving the dashboard.

### Acceptance criteria
- [ ] Sidebar "Files" section lists all `.md` files under `plans/<active_feature>/`.
- [ ] Clicking a file sends a `GET /api/files/{filename}` request and loads the content into `fileStore`.
- [ ] A markdown card appears in the chat panel showing the rendered content (headers, lists, code blocks).
- [ ] The card is visually distinct from chat messages (e.g. different background, filename as title).
- [ ] Asking "show me [filename]" or "show me the plan" in the chat triggers the same file load + card render.

### Edge cases
- File is empty: card renders with placeholder text "This file is empty."
- File is not found (404): chat shows an inline error message, not a page crash.
- Feature has no MD files: Files section shows "No files yet."

**Delivered by:** Conv 4 (S4)

---

## S5 — Chat grounded in current STATE.json

**As a** developer using Pathly,
**I want to** ask the chat "what's next?" (or any question about the feature) and get an answer based on the current pipeline state,
**so that** I always have up-to-date context without reading raw JSON files.

### Acceptance criteria
- [ ] Sending a chat message calls `POST /api/chat` with the message and the current STATE.json payload.
- [ ] The server proxies the request to Claude API, including STATE.json as context.
- [ ] The response streams back to the chat panel (tokens appear as they arrive).
- [ ] "What's next?" produces a response that references the current stage and remaining conversations.
- [ ] If the Claude API call fails, the chat shows an error message inline (not a page crash).

### Edge cases
- Claude API key not set: server returns 503 with a human-readable error, chat shows it.
- STATE.json is missing: server sends an empty-state context; Claude's answer acknowledges no feature is active.
- Network timeout mid-stream: chat shows partial response followed by an error indicator.

**Delivered by:** Conv 4 (S5)

---

## S6 — Go / Pause buttons trigger CLI actions

**As a** developer using Pathly,
**I want to** click [Go] or [Pause] in the UI to start or pause the pipeline,
**so that** I never need to switch to a terminal for common control actions.

### Acceptance criteria
- [ ] A [Go] button and a [Pause] button are visible in the top header at all times.
- [ ] Clicking [Go] sends `POST /api/go`; the server runs `pathly go` as a subprocess.
- [ ] Clicking [Pause] sends `POST /api/pause`; the server runs `pathly pause` as a subprocess.
- [ ] While an action is in flight, the corresponding button is disabled and shows a loading indicator.
- [ ] The action result (success or error output) appears as a message in the chat panel.
- [ ] [Go] is disabled when `STATE.json → current` is already in an active running state.
- [ ] [Pause] is disabled when `STATE.json → current` is IDLE or DONE.

### Edge cases
- Subprocess exits non-zero: the server returns the stderr as a 400 response; chat shows the error.
- Double-click before first response: second request is silently ignored (button already disabled).

**Delivered by:** Conv 3 (S6)

---

## S7 — Agent status indicators in sidebar

**As a** developer using Pathly,
**I want to** see which agents (builder, tester, discoverer) are running or idle in the sidebar,
**so that** I know what the system is doing right now without reading logs.

### Acceptance criteria
- [ ] Sidebar "Agents" section shows a row per known agent role (at minimum: builder, tester, discoverer/planner).
- [ ] Each row has a coloured dot: green = running, grey = idle.
- [ ] Agent status is derived from the most recent SSE event (`last_actor` field of STATE.json).
- [ ] Status updates within 1 second of a new event arriving on the SSE stream.

### Edge cases
- `last_actor` is null: all agents shown as idle.
- SSE connection drops: dots freeze in last-known state; a "reconnecting…" banner appears.

**Delivered by:** Conv 3 (S7)

---

## S8 — Real-time board updates via SSE

**As a** developer using Pathly,
**I want** the board to update automatically as EVENTS.jsonl changes,
**so that** I see live progress without ever refreshing the browser.

### Acceptance criteria
- [ ] `GET /api/events` is an SSE stream that emits one JSON event per new line appended to EVENTS.jsonl.
- [ ] The React client connects to the SSE stream on mount using `EventSource`.
- [ ] A new event received on the stream updates `featureStore` (stage, last_actor, conversations) within 500ms.
- [ ] If the SSE connection drops, the client automatically reconnects with exponential back-off (max 30s).
- [ ] A new EVENTS.jsonl line written by the CLI is visible in the board within 2 seconds end-to-end.

### Edge cases
- EVENTS.jsonl does not exist: SSE stream opens and stays open; emits no events until the file is created.
- Malformed JSON line in EVENTS.jsonl: server logs the parse error and continues tailing (does not crash or close the stream).
- Multiple browser tabs open: each tab maintains its own SSE connection independently.

**Delivered by:** Conv 1 (S8 — backend); Conv 2 (S8 — frontend SSE hook)
