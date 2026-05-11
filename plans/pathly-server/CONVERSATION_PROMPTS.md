# pathly-server — Conversation Prompts

Each prompt below is a self-contained implementation task. Copy the prompt block
into a builder session. Complete one conversation fully before starting the next.

Story ID cross-reference: see USER_STORIES.md.

---

## Conv 1 — FastAPI backend + SSE watcher

**Stories delivered:** S8 (backend)

```text
Implement pathly-server Conv 1 from plans/pathly-server/IMPLEMENTATION_PLAN.md.

Working directory: pathly-engine/

Goal: create the FastAPI server package with all API routes and the EVENTS.jsonl
SSE watcher. No UI is involved in this conversation.

--- Files to create ---

server/__init__.py
  Empty package marker.

server/watcher.py
  async def tail_events(filepath: str) -> AsyncGenerator[str, None]:
    - Open filepath for reading. If the file does not exist, wait (polling
      every 0.25 s) until it appears, then open it.
    - Seek to end of file on first open.
    - In a loop: read all new lines; for each non-empty stripped line yield
      it; then sleep 0.1 s.
    - Must not crash or close the generator on a JSONDecodeError — log the
      bad line and continue.
    - Must handle the file being replaced (log rotation): re-open when an
      OSError occurs on read.

server/main.py
  FastAPI app. All routes listed below. The active feature is resolved by
  reading the most recently modified STATE.json under plans/*/STATE.json.
  If none exists, the "active feature" is None.

  GET /api/state
    Read plans/<active_feature>/STATE.json. Return its contents as JSON.
    If no active feature: return {"error": "no active feature"} with HTTP 200.
    If STATE.json is malformed: return {"error": "malformed state"} with HTTP 200.

  GET /api/files
    List all .md files directly inside plans/<active_feature>/.
    Return: {"feature": "<name>", "files": ["FILE1.md", "FILE2.md", ...]}
    Filenames only — no full paths.
    If no active feature: return {"feature": null, "files": []}.

  GET /api/files/{filename}
    Read plans/<active_feature>/<filename>.
    Return: {"filename": "<name>", "content": "<raw markdown string>"}
    Filename must end with .md; reject others with HTTP 400.
    If file not found: HTTP 404 with {"error": "not found"}.
    Path traversal guard: reject filenames containing "/" or "..".

  POST /api/go
    Run subprocess: ["pathly", "go"] with cwd = repo root.
    Capture stdout + stderr. Timeout: 60 s.
    Return: {"stdout": "...", "stderr": "...", "returncode": N}
    If subprocess times out: return {"error": "timeout"} with HTTP 504.
    If pathly binary not found: return {"error": "pathly not found"} with HTTP 500.

  POST /api/pause
    Same pattern as /api/go but runs ["pathly", "pause"].

  GET /api/events
    SSE endpoint using sse-starlette's EventSourceResponse.
    Resolves the EVENTS.jsonl path from the active feature.
    Calls tail_events(filepath) and yields each line as an SSE event with
    event type "event" and the raw JSONL line as data.
    If no active feature exists yet, stream stays open and emits nothing
    until an EVENTS.jsonl appears (the watcher handles this).

  CORS: add CORSMiddleware allowing all origins (needed for dev mode where
  the Vite dev server runs on a different port).

--- Verify ---

1. Start: cd pathly-engine && uvicorn server.main:app --port 8765 --reload
2. curl http://localhost:8765/api/state
   Expected: JSON object or {"error": "no active feature"}
3. curl http://localhost:8765/api/files
   Expected: {"feature": null, "files": []} or a real list
4. curl -N http://localhost:8765/api/events
   Expected: SSE stream opens and stays open (no immediate close)
5. In a separate shell, append a line to plans/<feature>/EVENTS.jsonl:
   echo '{"type":"test"}' >> plans/<feature>/EVENTS.jsonl
   Expected: the curl in step 4 prints: data: {"type":"test"}

After verification, update plans/pathly-server/PROGRESS.md Conv 1 to DONE.
```

---

## Conv 2 — React scaffold + Zustand stores + SSE hook

**Stories delivered:** S8 (frontend)

```text
Implement pathly-server Conv 2 from plans/pathly-server/IMPLEMENTATION_PLAN.md.

Working directory: pathly-engine/ui/  (create this directory)

Goal: scaffold the Vite + React project, define the three Zustand stores, wire
the SSE connection in featureStore, and render a three-column layout shell.
No real UI components yet — placeholders only.

--- Prerequisites ---
Conv 1 must be complete and the FastAPI server must be running on port 8765
during the verify step.

--- Files to create ---

ui/package.json
  {
    "name": "pathly-ui",
    "version": "0.1.0",
    "private": true,
    "scripts": {
      "dev": "vite --port 5173",
      "build": "tsc && vite build",
      "preview": "vite preview"
    },
    "dependencies": {
      "react": "^18.2.0",
      "react-dom": "^18.2.0",
      "zustand": "^4.5.0",
      "react-markdown": "^9.0.0"
    },
    "devDependencies": {
      "@types/react": "^18.2.0",
      "@types/react-dom": "^18.2.0",
      "@vitejs/plugin-react": "^4.2.0",
      "typescript": "^5.4.0",
      "vite": "^5.2.0"
    }
  }

ui/vite.config.ts
  Standard Vite React config. Add a dev server proxy so all /api/* requests
  are forwarded to http://localhost:8765. This allows the dev server on 5173
  to talk to the FastAPI server on 8765 without CORS issues in dev mode.

ui/tsconfig.json
  Standard TypeScript config targeting ES2020, JSX react-jsx.

ui/index.html
  Standard Vite HTML entry point referencing src/main.tsx.

ui/src/main.tsx
  ReactDOM.createRoot + <App /> mount.

ui/src/stores/featureStore.ts
  Zustand store with:
    state shape:
      stage: string             // e.g. "IDLE", "PLAN", "BUILD", "REVIEW", "TEST", "DONE"
      activeFeature: string | null
      conversations: Array<{id: string; status: "TODO"|"IN_PROGRESS"|"DONE"}>
      lastEvent: Record<string, unknown> | null
      lastEventAt: string | null  // ISO timestamp of last received event
      error: string | null
      sseConnected: boolean

    actions:
      connectSSE(): void
        - Create an EventSource pointing at "/api/events".
        - On message: parse JSON; update lastEvent, lastEventAt; if the event
          has a "state" key, update stage and activeFeature from it.
        - On open: set sseConnected = true.
        - On error: set sseConnected = false; schedule reconnect with
          exponential back-off starting at 1s, doubling each attempt, max 30s.
        - Call connectSSE() once on store initialisation (outside the store
          definition, after create()).
      fetchState(): Promise<void>
        - GET /api/state; update stage, activeFeature, conversations from
          the response. Sets error on failure.

ui/src/stores/fileStore.ts
  Zustand store with:
    state shape:
      fileList: string[]         // filenames only
      selectedFile: string | null
      fileContent: string | null  // raw markdown
      loading: boolean
      error: string | null

    actions:
      fetchFileList(): Promise<void>
        GET /api/files → set fileList.
      loadFile(filename: string): Promise<void>
        GET /api/files/{filename} → set selectedFile + fileContent.
        Set loading true before request, false after.

ui/src/stores/chatStore.ts
  Zustand store with:
    state shape:
      messages: Array<{role: "user"|"assistant"; content: string; isMarkdownCard?: boolean}>
      streaming: boolean
      pendingAction: string | null   // "go" | "pause" | null

    actions:
      addMessage(role, content, isMarkdownCard?): void
      setStreaming(v: boolean): void
      setPendingAction(action: string | null): void
      sendMessage(text: string): Promise<void>
        - Appends user message.
        - Sets streaming = true.
        - POST /api/chat {message: text, state: featureStore.getState().lastEvent}
          with streaming fetch (ReadableStream).
        - Appends assistant message tokens as they arrive.
        - Sets streaming = false when done.

ui/src/App.tsx
  Three-column flexbox layout: <Sidebar />, <Board />, <ChatPanel />.
  Each is a placeholder div with the column name in grey text.
  Header bar with "Pathly" title and placeholder [Go] [Pause] buttons.
  On mount: call featureStore.connectSSE() and featureStore.fetchState()
  and fileStore.fetchFileList().

ui/src/components/Sidebar.tsx   (placeholder — empty div)
ui/src/components/Board.tsx     (placeholder — empty div)
ui/src/components/ChatPanel.tsx (placeholder — empty div)

--- Verify ---

1. cd pathly-engine/ui && npm install && npm run dev
2. Open http://localhost:5173 in browser.
   Expected: three-column layout visible, header shows "Pathly".
3. Open DevTools → Network → Filter by "events".
   Expected: a long-lived SSE connection to /api/events with status 200.
4. Open DevTools → Application → Zustand (or console):
   window.__ZUSTAND_FEATURE_STORE__ should be accessible if you expose stores.
   At minimum: no console errors on load.

After verification, update plans/pathly-server/PROGRESS.md Conv 2 to DONE.
```

---

## Conv 3 — Sidebar + Board components

**Stories delivered:** S2, S3, S6, S7

```text
Implement pathly-server Conv 3 from plans/pathly-server/IMPLEMENTATION_PLAN.md.

Working directory: pathly-engine/ui/src/

Goal: replace the placeholder Sidebar and Board components with real
implementations. Wire Go/Pause buttons. No chat functionality yet.

--- Prerequisites ---
Conv 2 must be complete (stores exist and SSE is connected).

--- Files to modify ---

ui/src/components/Sidebar.tsx
  Replace the placeholder. Render three sections:

  1. Features section
     - Heading "Features".
     - Read activeFeature from featureStore.
     - If null: show "No active feature."
     - If set: show the feature name with an arrow/bullet indicating it is
       active. (Static list for now — only the active feature is shown.
       Expanding to multi-feature listing is out of scope for this conv.)

  2. Files section
     - Heading "Files".
     - Read fileList from fileStore.
     - If empty: show "No files yet."
     - Otherwise: render each filename as a clickable row.
     - On click: call fileStore.loadFile(filename).
     - Highlight the selected file (fileStore.selectedFile).

  3. Agents section
     - Heading "Agents".
     - Show rows for: planner, builder, tester (hardcoded agent names).
     - Derive status from featureStore.lastEvent?.last_actor:
         if last_actor === agentName → "running" (green dot)
         else → "idle" (grey dot)
     - If featureStore.sseConnected === false: show a "reconnecting…"
       banner above the agents list.

ui/src/components/Board.tsx
  Replace the placeholder. Implement the Kanban board:

  STAGE_ORDER = ["PLAN", "BUILD", "REVIEW", "TEST", "DONE"]

  - Render five columns side by side.
  - The column matching featureStore.stage is "active":
      bold column header, 2px accent border (blue or green).
  - Stages before the active one are "done": header has a check-mark prefix,
      column body is dimmed (opacity 0.5).
  - Stages after the active one are "pending": header is normal, column body
      is dimmed.
  - Conversation cards:
      - Read featureStore.conversations.
      - Each card belongs in the column matching the stage its status implies:
          DONE cards → in the stage column they completed (if stage info is
          available) OR in the active stage column.
          IN_PROGRESS card → in the active stage column.
          TODO cards → in the active stage column (future convs).
      - Status icons: ○ = TODO, ⟳ = IN_PROGRESS, ✓ = DONE.
      - Card shows the conversation id.
  - If no active feature: show "No active feature" centred across all columns.
  - Last event timestamp: below the board, show
    "Last event: <relative time>" using featureStore.lastEventAt.
    If null: show "No events yet."

ui/src/App.tsx  (modify)
  Replace placeholder [Go] and [Pause] buttons with wired versions:

  Go button:
    - Disabled when featureStore.stage is "PLANNING", "BUILD", "REVIEW", "TEST"
      (i.e., already running) OR when chatStore.pendingAction is not null.
    - On click: set chatStore.pendingAction = "go"; POST /api/go; append
      result to chatStore messages; clear pendingAction.
    - While in flight: button shows "Starting…" and is disabled.

  Pause button:
    - Disabled when featureStore.stage is "IDLE" or "DONE"
      OR when chatStore.pendingAction is not null.
    - On click: set chatStore.pendingAction = "pause"; POST /api/pause;
      append result to chatStore messages; clear pendingAction.
    - While in flight: button shows "Pausing…" and is disabled.

--- Verify ---

1. Start FastAPI (Conv 1) and Vite dev server (Conv 2).
2. Ensure plans/<feature>/STATE.json exists with a real state.
3. Open http://localhost:5173.
   Expected:
   - Sidebar shows the active feature name.
   - Files section lists .md filenames.
   - Board shows five columns; active stage column is highlighted.
   - Conversation cards appear in the active column.
4. Append a line to EVENTS.jsonl with last_actor = "builder".
   Expected: builder dot turns green within 1 s.
5. Click a file in the sidebar.
   Expected: fileStore.selectedFile is set (verify in console if needed).
6. Click [Go] button.
   Expected: button disables, POST /api/go fires (check Network tab).

After verification, update plans/pathly-server/PROGRESS.md Conv 3 to DONE.
```

---

## Conv 4 — Chat panel + markdown file preview

**Stories delivered:** S4, S5

```text
Implement pathly-server Conv 4 from plans/pathly-server/IMPLEMENTATION_PLAN.md.

Working directory: pathly-engine/ (both server/ and ui/src/)

Goal: implement the chat panel with streaming Claude responses, and inline
markdown file preview cards.

--- Prerequisites ---
Conv 3 must be complete. Claude API key must be available as environment
variable ANTHROPIC_API_KEY on the server process.

--- Files to modify/create ---

server/main.py  (add one endpoint)
  POST /api/chat
    Request body: {message: string, state: object | null}
    - If ANTHROPIC_API_KEY env var is not set: return HTTP 503
      {"error": "ANTHROPIC_API_KEY not configured"}.
    - Build a system prompt:
        "You are a Pathly assistant. The user is working on a software feature
         pipeline. Here is the current pipeline state:\n\n<state JSON>\n\n
         Answer questions about the feature, its progress, and what comes next.
         Be concise. If asked to show a file, say which file to load."
    - Call the Anthropic messages API with stream=True using the anthropic
      Python SDK (model: claude-haiku-3-5-latest or claude-3-haiku-20240307).
    - Return an SSE response (sse-starlette EventSourceResponse) streaming
      each text delta as: event type "delta", data = the token string.
    - On completion: emit event type "done", data = "".
    - On Anthropic API error: emit event type "error", data = error message.

ui/src/components/ChatPanel.tsx  (replace placeholder)
  Implement the full chat panel:

  Message list area (scrollable, takes most of the height):
    - Renders chatStore.messages in order.
    - User messages: right-aligned, styled differently from assistant.
    - Assistant messages: left-aligned.
    - If message.isMarkdownCard === true: render the content using
      react-markdown inside a card element (border, rounded corners, filename
      as card title if available).
    - If chatStore.streaming === true: show a blinking cursor after the last
      assistant message.
    - Auto-scroll to bottom on new message or new token.

  Input area (pinned to bottom):
    - Text input (multiline textarea, Shift+Enter = newline, Enter = send).
    - Send button: disabled while streaming.
    - On send:
        1. Check if the message matches /show me (.+)/i.
           If yes: extract the filename (strip spaces, ensure .md suffix if
           missing); call fileStore.loadFile(filename); then add a markdown
           card message to chatStore using the loaded fileContent.
           Do NOT call /api/chat for pure "show me" messages.
        2. Otherwise: call chatStore.sendMessage(text).

  File preview watcher:
    - useEffect watching fileStore.selectedFile + fileStore.fileContent.
    - When selectedFile changes and fileContent is loaded: add a markdown
      card message to chatStore (role "assistant", isMarkdownCard true,
      content = fileContent).
    - This ensures sidebar clicks also trigger inline preview.

chatStore.sendMessage implementation (finalize in this conv):
  - POST /api/chat with fetch + ReadableStream.
  - Parse SSE chunks manually:
      Split on "\n\n"; for each chunk parse "event: X\ndata: Y".
      On event "delta": append Y to the streaming assistant message.
      On event "done": set streaming = false.
      On event "error": append error text; set streaming = false.
  - Handle network errors: append error message to chat; set streaming = false.

--- Verify ---

1. Ensure ANTHROPIC_API_KEY is set in your shell.
2. Start FastAPI and Vite dev server.
3. Open http://localhost:5173.
4. Type "what's next?" and press Enter.
   Expected: streaming tokens appear one by one in the chat panel.
5. Click a file in the sidebar (e.g. USER_STORIES.md).
   Expected: a markdown card appears in the chat panel with rendered headers
   and lists. Card has the filename as its title.
6. Type "show me PROGRESS.md" and press Enter.
   Expected: PROGRESS.md content loads and renders as a card.
7. Stop the FastAPI server. Type another message.
   Expected: chat shows an error message inline, does not crash.

After verification, update plans/pathly-server/PROGRESS.md Conv 4 to DONE.
```

---

## Conv 5 — Production build + `pathly server` command

**Stories delivered:** S1

```text
Implement pathly-server Conv 5 from plans/pathly-server/IMPLEMENTATION_PLAN.md.

Working directory: pathly-engine/

Goal: wire together the production build so that `pathly server` starts
everything in one command with no separate npm or uvicorn steps.

--- Prerequisites ---
Conv 1–4 must be complete and all verified.

--- Files to create/modify ---

ui/vite.config.ts  (modify)
  Ensure the build output directory is set to "../ui/dist" relative to
  the ui/ directory — i.e. pathly-engine/ui/dist/. This keeps the bundle
  inside the package tree where FastAPI can find it.

server/main.py  (modify — add static file mount)
  At the bottom of the FastAPI app setup (after all API routes):

  import pathlib
  UI_DIST = pathlib.Path(__file__).parent.parent / "ui" / "dist"
  if UI_DIST.exists():
      from fastapi.staticfiles import StaticFiles
      app.mount("/", StaticFiles(directory=str(UI_DIST), html=True), name="ui")

  The html=True flag makes FastAPI serve index.html for unknown routes,
  enabling React Router client-side navigation.

  Note: API routes defined BEFORE the mount take priority over static files.
  Verify that /api/* routes still work after adding the mount.

server/run.py  (create)
  import subprocess, sys, time, webbrowser, socket

  PORT = 8765
  HOST = "127.0.0.1"
  URL  = f"http://{HOST}:{PORT}"

  def port_in_use(port: int) -> bool:
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
          return s.connect_ex((HOST, port)) == 0

  def run():
      if port_in_use(PORT):
          print(f"Error: port {PORT} is already in use. Is pathly server already running?")
          sys.exit(1)

      print(f"Starting Pathly dashboard on {URL} ...")
      proc = subprocess.Popen(
          [sys.executable, "-m", "uvicorn", "server.main:app",
           "--host", HOST, "--port", str(PORT)],
          cwd=<repo root resolved at runtime>
      )
      # Wait for server to become ready (poll up to 10 s)
      for _ in range(40):
          time.sleep(0.25)
          if port_in_use(PORT):
              break
      else:
          proc.terminate()
          print("Error: server failed to start within 10 seconds.")
          sys.exit(1)

      print(f"Pathly dashboard ready at {URL}")
      webbrowser.open(URL)

      try:
          proc.wait()
      except KeyboardInterrupt:
          print("\nShutting down Pathly dashboard...")
          proc.terminate()
          proc.wait()
          print("Stopped.")

engine_cli/__main__.py  (modify)
  Add "server" to the command dispatch:

  from server.run import run as cmd_server

  elif command == "server":
      cmd_server()

  Update the usage string to include "server" in the Commands list.

pyproject.toml  (modify)
  Add to [project.dependencies]:
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "sse-starlette>=1.8.0",
    "anthropic>=0.28.0",

  Add server* to [tool.setuptools.packages.find] include list.

--- Build step (run manually before verify) ---
  cd pathly-engine/ui && npm run build
  Expected: ui/dist/ is created with index.html + assets/.

--- Verify (full smoke test) ---

1. cd pathly-engine && pip install -e ".[dev]" (or pip install -e .)
2. pathly server
   Expected:
   - Prints "Starting Pathly dashboard on http://127.0.0.1:8765 ..."
   - Prints "Pathly dashboard ready at http://127.0.0.1:8765"
   - Default browser opens to http://127.0.0.1:8765.
   - Board shows real data from STATE.json.
3. Append a line to plans/<feature>/EVENTS.jsonl.
   Expected: board updates within 2 seconds without a page refresh.
4. Press Ctrl+C.
   Expected: prints "Stopped." and process exits cleanly.
5. Run pathly server again immediately (port should be free).
   Expected: starts normally.
6. Manually bind port 8765 in another shell:
     python -c "import socket,time; s=socket.socket(); s.bind(('127.0.0.1',8765)); s.listen(1); time.sleep(30)"
   Then run pathly server.
   Expected: prints human-readable error and exits with code 1.

After verification, update plans/pathly-server/PROGRESS.md Conv 5 to DONE.
```
