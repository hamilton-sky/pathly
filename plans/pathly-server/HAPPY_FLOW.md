# pathly-server — Happy Flow (Golden Path)

**Feature:** pathly-server
**Scenario:** A developer monitors and controls the `auth-feature` pipeline from
first launch through completion.
**Used by:** Tester — use each step's "Verify" checklist to write acceptance tests.

---

## Preconditions

Before the flow begins, all of the following must be true:

1. `pathly-engine` is installed (`pip install -e .` or equivalent).
2. The `pathly` CLI command resolves in the shell (`pathly --version` prints a version).
3. A feature named `auth-feature` exists with the following files:
   - `plans/auth-feature/STATE.json` — valid JSON (see system state at Step 1).
   - `plans/auth-feature/EVENTS.jsonl` — exists; contains at least one line.
   - `plans/auth-feature/USER_STORIES.md`, `IMPLEMENTATION_PLAN.md` — present (any content).
4. `ANTHROPIC_API_KEY` is set in the environment.
5. Port 8765 is not in use.
6. A modern browser is available and is the system default.

### Initial STATE.json (before Step 1)

```json
{
  "feature": "auth-feature",
  "current": "BUILD",
  "last_actor": null,
  "conversations": [
    {"id": "conv-1", "status": "DONE"},
    {"id": "conv-2", "status": "IN_PROGRESS"},
    {"id": "conv-3", "status": "TODO"}
  ],
  "updated_at": "2026-05-11T09:00:00Z"
}
```

### Initial EVENTS.jsonl (before Step 1)

```
{"type":"stage_change","stage":"BUILD","last_actor":"builder","ts":"2026-05-11T09:00:00Z"}
{"type":"conv_done","conv_id":"conv-1","last_actor":"builder","ts":"2026-05-11T09:15:00Z"}
{"type":"conv_started","conv_id":"conv-2","last_actor":"builder","ts":"2026-05-11T09:16:00Z"}
```

---

## Step-by-step golden path

---

### Step 1 — Run `pathly server`

**User action:** Opens a terminal and runs:
```
pathly server
```

**What the user sees (terminal):**
```
Starting Pathly dashboard on http://127.0.0.1:8765 ...
Pathly dashboard ready at http://127.0.0.1:8765
```
The default browser opens automatically to `http://127.0.0.1:8765`.

**System state at this step:**
- `STATE.json` — unchanged from preconditions.
- `EVENTS.jsonl` — unchanged from preconditions.
- FastAPI process is running on port 8765.
- SSE watcher is tailing `plans/auth-feature/EVENTS.jsonl`.

**Expected UI state at this step:**
- Page title or header reads "Pathly".
- Three-column layout is visible: Sidebar (left), Board (center), Chat Panel (right).
- Header shows [Go] and [Pause] buttons.
  - [Go] is **disabled** (feature is already in BUILD stage — running state).
  - [Pause] is **enabled**.
- Sidebar — Features section: "auth-feature" is shown as the active feature.
- Sidebar — Files section: lists "USER_STORIES.md" and "IMPLEMENTATION_PLAN.md".
- Sidebar — Agents section: all three agents (planner, builder, tester) show grey dots
  (last_actor is null in STATE.json).
- Board — BUILD column is **highlighted** (bold header, accent border).
- Board — PLAN column shows a check-mark prefix and is dimmed (completed stage).
- Board — REVIEW, TEST, DONE columns are dimmed (pending stages).
- Board — Conversation cards in the BUILD column:
  - conv-1: ✓ (DONE)
  - conv-2: ⟳ (IN_PROGRESS)
  - conv-3: ○ (TODO)
- Below the board: "Last event: a moment ago" (relative time from the most recent
  EVENTS.jsonl line).
- Chat panel — message list is empty; input placeholder reads something like
  "Ask about the feature…".

**Verify:**
- [ ] Terminal printed both expected lines before browser opened.
- [ ] Browser opened within 2 seconds of the "ready" line.
- [ ] No console errors in browser DevTools.
- [ ] DevTools Network tab shows an open SSE connection to `/api/events`.

---

### Step 2 — User asks "what's next?" in chat

**User action:** Clicks the chat input, types `what's next?`, presses Enter.

**What the user sees:**
- A right-aligned user message bubble appears: "what's next?"
- A blinking cursor appears below it (streaming indicator).
- Tokens start appearing in a left-aligned assistant message. Example response:
  > "You're currently in the **BUILD** stage. conv-2 is in progress. Once conv-2
  > completes, conv-3 is next (currently TODO). After conv-3 finishes, the pipeline
  > will move to REVIEW."
- Blinking cursor disappears when the response ends.

**System state at this step:**
- `STATE.json` — unchanged.
- `EVENTS.jsonl` — unchanged.
- A POST request was made to `/api/chat` with `{message: "what's next?", state: <last event>}`.
- The Anthropic API was called with the STATE.json context in the system prompt.

**Expected UI state at this step:**
- Chat panel shows: user message + streaming assistant response.
- Board, Sidebar — unchanged; no re-render triggered by a chat message.
- [Go] still disabled; [Pause] still enabled.

**Verify:**
- [ ] DevTools Network: POST to `/api/chat` returns status 200 with content-type `text/event-stream`.
- [ ] Tokens appear incrementally (not all at once).
- [ ] Response text references "BUILD", "conv-2", and "conv-3".
- [ ] Streaming cursor disappears on completion.
- [ ] No page crash or error toast.

---

### Step 3 — User clicks a file in the sidebar

**User action:** Clicks "IMPLEMENTATION_PLAN.md" in the Sidebar — Files section.

**What the user sees:**
- The filename is highlighted in the sidebar (selected state).
- A markdown card appears in the chat panel below the previous assistant message.
  - Card has a distinct visual style (different background, border, rounded corners).
  - Card title shows "IMPLEMENTATION_PLAN.md".
  - Card body renders the file content with markdown formatting: headers, lists,
    code blocks.

**System state at this step:**
- `STATE.json` — unchanged.
- `EVENTS.jsonl` — unchanged.
- A GET request was made to `/api/files/IMPLEMENTATION_PLAN.md`.
- `fileStore.selectedFile` = "IMPLEMENTATION_PLAN.md".
- `fileStore.fileContent` = raw markdown string.

**Expected UI state at this step:**
- Chat panel now shows: user message → assistant response → markdown file card.
- The file card is visually distinct from chat messages.
- Chat auto-scrolled to show the card.
- Board and Sidebar agents section — unchanged.

**Verify:**
- [ ] DevTools Network: GET `/api/files/IMPLEMENTATION_PLAN.md` returns 200 with `{"filename": "IMPLEMENTATION_PLAN.md", "content": "..."}`.
- [ ] The rendered card has the filename as its title.
- [ ] Markdown headings and lists are rendered (not raw `#` or `-` characters).
- [ ] Chat panel scrolled to the bottom automatically.

---

### Step 4 — conv-2 completes (SSE event arrives)

**User action:** None. The builder agent finishes conv-2 and writes to EVENTS.jsonl.
(In a test: append the following line to `plans/auth-feature/EVENTS.jsonl`.)

```json
{"type":"conv_done","conv_id":"conv-2","stage":"BUILD","last_actor":"builder","ts":"2026-05-11T10:00:00Z","state":{"feature":"auth-feature","current":"REVIEW","conversations":[{"id":"conv-1","status":"DONE"},{"id":"conv-2","status":"DONE"},{"id":"conv-3","status":"TODO"}]}}
```

**What the user sees:**
- Within 2 seconds, without any page refresh:
  - Board: conv-2 card icon changes from ⟳ to ✓.
  - Board: the highlighted column shifts from **BUILD** to **REVIEW**.
    BUILD column now has a check-mark prefix and is dimmed.
    REVIEW column is now bold with accent border.
  - Sidebar — Agents section: builder dot turns **green** (last_actor = "builder").
  - Below board: "Last event: a moment ago" timestamp updates.

**System state at this step:**
- `STATE.json` — still on disk as-was (the engine may or may not have updated it;
  the board is driven by EVENTS.jsonl SSE events, not by polling STATE.json).
- `EVENTS.jsonl` — now has a fourth line (the one appended above).

**Expected UI state at this step:**
- Board: PLAN ✓ dimmed, BUILD ✓ dimmed, **REVIEW highlighted**, TEST dimmed, DONE dimmed.
- Conversation cards (in REVIEW column): conv-1 ✓, conv-2 ✓, conv-3 ○.
- [Go] button transitions from disabled to **enabled** (REVIEW stage is not an
  actively running state in the same sense; Go would advance to the next
  conversation).
- [Pause] remains enabled.

**Verify:**
- [ ] Board re-renders within 2 seconds of the file write (no page refresh).
- [ ] conv-2 card shows ✓ (not ⟳).
- [ ] REVIEW column is highlighted; BUILD column is dimmed.
- [ ] Builder agent dot is green.
- [ ] No page crash or console error during the update.

---

### Step 5 — User clicks [Go] to start conv-3

**User action:** Clicks the [Go] button in the header.

**What the user sees:**
- [Go] button immediately shows "Starting…" and becomes disabled.
- [Pause] also disables while the action is in flight.
- Within a few seconds, a new message appears at the bottom of the chat panel:
  > System: `pathly go` completed (exit 0)
  > stdout: [output from pathly go]
- [Go] re-disables (conv-3 is now IN_PROGRESS — running state).
- [Pause] re-enables.

**What happens in the background:**
- POST to `/api/go`.
- Server runs `subprocess.run(["pathly", "go"])`.
- pathly engine starts conv-3; writes to EVENTS.jsonl.

**System state at this step:**
- `EVENTS.jsonl` — new line(s) appended by pathly engine:
  ```json
  {"type":"conv_started","conv_id":"conv-3","last_actor":"builder","ts":"2026-05-11T10:01:00Z","state":{"current":"BUILD","conversations":[...]}}
  ```
- `STATE.json` — updated by engine: conv-3 = IN_PROGRESS.

**Expected UI state at this step:**
- Board: BUILD column re-highlighted (pathly re-entered BUILD for conv-3).
- conv-3 card shows ⟳.
- Chat panel: new system message showing go command result.
- [Go] disabled; [Pause] enabled.

**Verify:**
- [ ] DevTools Network: POST `/api/go` returns 200 with `{"stdout": "...", "stderr": "...", "returncode": 0}`.
- [ ] Button shows "Starting…" while in flight, then reverts to "Go" (disabled).
- [ ] Chat panel has a new message with the command result.
- [ ] Board updates to show conv-3 as IN_PROGRESS.

---

### Step 6 — All conversations complete; pipeline reaches DONE

**User action:** None. The engine completes conv-3 and the pipeline finishes.
(In a test: append these two lines to EVENTS.jsonl.)

```json
{"type":"conv_done","conv_id":"conv-3","last_actor":"builder","ts":"2026-05-11T10:30:00Z","state":{"current":"DONE","conversations":[{"id":"conv-1","status":"DONE"},{"id":"conv-2","status":"DONE"},{"id":"conv-3","status":"DONE"}]}}
{"type":"stage_change","stage":"DONE","last_actor":"builder","ts":"2026-05-11T10:30:01Z"}
```

**What the user sees:**
- Board: DONE column becomes highlighted.
- All five columns to the left of DONE have check-mark prefixes and are dimmed.
- All three conversation cards show ✓.
- Sidebar — builder dot is green (last_actor = "builder").

**System state at this step:**
- `STATE.json` (if updated by engine):
  ```json
  {
    "feature": "auth-feature",
    "current": "DONE",
    "last_actor": "builder",
    "conversations": [
      {"id": "conv-1", "status": "DONE"},
      {"id": "conv-2", "status": "DONE"},
      {"id": "conv-3", "status": "DONE"}
    ],
    "updated_at": "2026-05-11T10:30:01Z"
  }
  ```
- `EVENTS.jsonl` — now contains 7 total lines (all appended during the flow).

**Expected UI state at this step:**
- Board: all five columns shown; **DONE** highlighted with accent; all others dimmed.
- [Go] is **disabled**.
- [Pause] is **disabled**.

**Verify:**
- [ ] DONE column is highlighted.
- [ ] All conversation cards show ✓.
- [ ] Both [Go] and [Pause] are disabled.

---

### Step 7 — User clicks [Pause] (disabled state)

**User action:** Attempts to click the [Pause] button.

**What the user sees:**
- The button does not respond to click (it is visually greyed out and the cursor
  shows a not-allowed style or the button ignores the event).
- No POST to `/api/pause` is made.
- The UI shows a tooltip or helper text explaining why the button is disabled.
  Acceptable text examples:
  - "Pipeline is already complete."
  - "Nothing is running — pause is not available."
- No error message; no crash.

**System state at this step:**
- `STATE.json` — unchanged from Step 6.
- `EVENTS.jsonl` — unchanged from Step 6.

**Expected UI state at this step:**
- [Pause] button has `disabled` attribute (HTML), preventing click.
- [Go] button also has `disabled` attribute.
- No network requests triggered.

**Verify:**
- [ ] DevTools Network: no POST to `/api/pause` when the button is clicked.
- [ ] Button has the `disabled` HTML attribute or equivalent (aria-disabled).
- [ ] No console errors on click attempt.
- [ ] A tooltip or adjacent text is visible explaining the disabled state
      (text content must mention "complete", "done", or "nothing running").

---

## Full flow summary table

| Step | User action | Key state change | Board highlight | Go | Pause |
|------|-------------|-----------------|-----------------|-----|-------|
| 1 | `pathly server` | Server starts | BUILD | disabled | enabled |
| 2 | "what's next?" chat | Claude API call | BUILD (unchanged) | disabled | enabled |
| 3 | Click IMPLEMENTATION_PLAN.md | File loaded into chat | BUILD (unchanged) | disabled | enabled |
| 4 | (engine event) conv-2 done | SSE → REVIEW stage | REVIEW | enabled | enabled |
| 5 | Click [Go] | subprocess pathly go; conv-3 starts | BUILD | disabled | enabled |
| 6 | (engine event) all done | SSE → DONE stage | DONE | disabled | disabled |
| 7 | Click [Pause] (disabled) | No action | DONE | disabled | disabled |

---

## Edge cases tested in this flow

| Scenario | Where covered | Expected behaviour |
|----------|---------------|--------------------|
| SSE connection drives board updates (no polling) | Steps 4, 6 | Board updates within 2 s of file write |
| [Go] disabled while feature is running | Steps 1, 5 | Button not clickable; no duplicate requests |
| [Pause] disabled when DONE | Step 7 | Button not clickable; explanation visible |
| Markdown file rendered as card (not raw text) | Step 3 | react-markdown output; distinct card style |
| Streaming chat response | Step 2 | Tokens arrive incrementally; cursor shown |
| Command result shown in chat | Step 5 | stdout/stderr displayed as system message |
| Agent dot reflects last_actor | Steps 4, 6 | Builder dot goes green on builder events |
