# pathly-server — Architecture Proposal

**Feature:** pathly-server
**Scope:** FastAPI backend + React frontend served by a single `pathly server` command
**Status:** Proposal — reviewed before Conv 1 begins

---

## Layers and boundaries

```
Layer 1: pathly-engine CLI (existing)
  engine_cli/__main__.py — add "server" subcommand (Conv 5 only)
  orchestrator/, runners/, team_flow/ — unchanged; their output files are read by Layer 2

Layer 2: FastAPI server (new — server/ package inside pathly-engine/)
  server/main.py         — FastAPI app; mounts React static bundle; all /api/* routes
  server/routes/         — (optional refactor) state.py, files.py, commands.py, chat.py
  server/watcher.py      — asyncio tail of EVENTS.jsonl; yields new lines to SSE clients
  server/chat_proxy.py   — streams Anthropic API responses back to the browser
  server/run.py          — subprocess launcher; port-in-use check; opens browser

Layer 3: React frontend (new — ui/ directory inside pathly-engine/)
  ui/src/stores/         — featureStore.ts, fileStore.ts, chatStore.ts (Zustand)
  ui/src/components/     — Sidebar.tsx, Board.tsx, ChatPanel.tsx, TicketCard.tsx,
                           FilePreviewCard.tsx
  ui/src/App.tsx         — root layout; header with Go/Pause buttons
  ui/src/main.tsx        — ReactDOM entry point
  ui/dist/               — production bundle; served by FastAPI as static files
```

---

## Dependency rules (enforce these in code review)

1. **Layer 3 → Layer 2 only via HTTP/SSE.**
   React never imports Python modules. All data flows through `/api/*` endpoints or
   the `/api/events` SSE stream. There are no shared files between `ui/` and `server/`.

2. **Layer 2 → Layer 1 only via subprocess or file reads.**
   FastAPI never imports from `engine_cli`, `orchestrator`, `runners`, or `team_flow`.
   CLI actions (go, pause) are executed with `subprocess.run(["pathly", ...])`.
   State is read from `plans/<feature>/STATE.json` and `plans/<feature>/EVENTS.jsonl`
   directly off disk. No engine functions are called.

3. **The `server/` package does not modify any existing engine module** except the
   single `elif command == "server":` dispatch added to `engine_cli/__main__.py`
   in Conv 5. All other engine files remain untouched.

4. **`ui/dist/` is a build artifact, not a source dependency.**
   FastAPI mounts `ui/dist/` only if the directory exists (conditional mount in
   `server/main.py`). The server starts and all `/api/*` routes work whether or not
   the React build has been run. This means Conv 1 can be verified independently.

5. **CORS is enabled in development.**
   `CORSMiddleware` allows all origins so that the Vite dev server on port 5173 can
   call the FastAPI server on port 8765. In production (`pathly server`), both are
   served from the same origin so CORS is not needed, but the middleware does no harm.

---

## Data flow diagrams

### SSE event pipeline (real-time board updates — S8)

```
EVENTS.jsonl (disk, append-only)
  → watcher.py: asyncio tail (polls every 0.1 s; waits for file creation if absent)
  → yields raw JSONL line string
  → GET /api/events: EventSourceResponse wraps each line as SSE event
  → EventSource in React featureStore.ts
  → featureStore.connectSSE(): parses JSON; updates stage, conversations, lastEvent
  → Board.tsx and Sidebar.tsx re-render via Zustand subscription
```

### CLI action pipeline (Go / Pause buttons — S6)

```
User clicks [Go] in header
  → chatStore.setPendingAction("go")
  → POST /api/go (FastAPI)
  → subprocess: pathly go (cwd = repo root, timeout 60 s)
  → pathly engine runs; writes new events to EVENTS.jsonl
  → watcher picks up new lines → SSE → featureStore updates
  → Board re-renders (stage, conversation status change)
  → /api/go returns {stdout, stderr, returncode}
  → chatStore.addMessage: result appended to chat panel
  → chatStore.setPendingAction(null); Go button re-enables
```

### Chat pipeline (grounded assistant — S5)

```
User types "what's next?" and presses Enter
  → chatStore.sendMessage(text)
  → Appends user message to chatStore.messages
  → POST /api/chat {message: text, state: featureStore.lastEvent}
  → server/chat_proxy.py (or inline in main.py):
      reads ANTHROPIC_API_KEY from env
      builds system prompt with STATE.json content
      calls Anthropic messages API with stream=True
      yields SSE events: event:"delta" data:<token>  …  event:"done" data:""
  → chatStore: appends tokens to streaming assistant message
  → ChatPanel.tsx re-renders with each token; auto-scrolls
  → On event:"done": chatStore.streaming = false; cursor removed
```

### File preview pipeline (inline markdown — S4)

```
User clicks filename in Sidebar
  → fileStore.loadFile(filename)
  → GET /api/files/{filename}
  → fileStore.selectedFile = filename; fileStore.fileContent = <raw markdown>
  → ChatPanel.tsx useEffect watching selectedFile:
      chatStore.addMessage("assistant", fileContent, isMarkdownCard=true)
  → react-markdown renders the content as a card inside the chat panel
```

---

## Key technology choices and rationale

| Choice | Rationale |
|--------|-----------|
| **SSE over WebSockets** | EVENTS.jsonl is append-only; push is one-directional (server → browser). SSE (EventSource) is simpler to implement, reconnects automatically, and requires no handshake protocol. WebSockets would add complexity with no benefit here. |
| **Subprocess for CLI actions** | FastAPI calls `pathly go` as a subprocess rather than importing engine internals. This enforces the Layer 2 → Layer 1 boundary and ensures the engine's own FSM and side effects run exactly as they do in CLI use. |
| **React build served by FastAPI** | Users run one command — `pathly server`. No Node.js is required at runtime. `npm run build` is a development-time step only. The `ui/dist/` bundle is committed or generated once; FastAPI serves it as static files. |
| **Zustand over Redux** | State shape is small: featureStore ~7 fields, fileStore ~5, chatStore ~3. Zustand avoids Redux boilerplate and integrates cleanly with React hooks at this scale. |
| **sse-starlette** | FastAPI-native SSE library. Integrates with asyncio and supports multiple simultaneous connections without threading. Chosen over manual `StreamingResponse` for cleaner event-type support. |
| **Vite + React + TypeScript** | Fast dev server with HMR. TypeScript catches store shape mismatches at build time. React's component model maps cleanly onto the Board/Sidebar/ChatPanel layout. |
| **anthropic Python SDK** | Official SDK; supports streaming with `stream=True`. Wrapping it in an SSE endpoint (chat_proxy) keeps the API key server-side and never exposes it to the browser. |

---

## Package additions to pyproject.toml

```toml
[project.dependencies]
# ... existing dependencies ...
"fastapi>=0.111.0",
"uvicorn[standard]>=0.29.0",
"sse-starlette>=1.8.0",
"anthropic>=0.28.0",
```

The `anthropic` SDK is added here rather than as a dev dependency because
`chat_proxy.py` calls the Anthropic API at runtime in production.

---

## New directory structure (after all 5 conversations)

```
pathly-engine/
  engine_cli/
    __main__.py          ← modified: add "server" subcommand dispatch (Conv 5)
  server/                ← new package (Conv 1–5)
    __init__.py
    main.py              ← FastAPI app; all /api/* routes; static mount
    watcher.py           ← asyncio EVENTS.jsonl tail; SSE generator
    chat_proxy.py        ← Anthropic streaming proxy
    run.py               ← uvicorn launcher; port check; browser open
  ui/                    ← new React app (Conv 2–5)
    src/
      stores/
        featureStore.ts  ← stage, conversations, SSE connection, fetchState
        fileStore.ts     ← fileList, selectedFile, fileContent, loadFile
        chatStore.ts     ← messages, streaming, pendingAction, sendMessage
      components/
        Sidebar.tsx      ← Features / Files / Agents sections
        Board.tsx        ← Kanban columns; conversation cards
        ChatPanel.tsx    ← message list; streaming render; markdown cards; input
        TicketCard.tsx   ← single conversation card (status icon + id)
        FilePreviewCard.tsx ← react-markdown card (used inside ChatPanel)
      App.tsx            ← root layout; Go/Pause header buttons
      main.tsx           ← ReactDOM entry point
    dist/                ← production bundle (generated by npm run build)
    package.json
    vite.config.ts       ← dev proxy /api/* → localhost:8765
    tsconfig.json
    index.html
  pyproject.toml         ← modified: new dependencies; server* in packages.find
```

---

## Conversation → layer mapping

| Conv | Primary layer touched | Files created or modified |
|------|-----------------------|---------------------------|
| 1 | Layer 2 — server/ | server/__init__.py, server/main.py, server/watcher.py |
| 2 | Layer 3 — ui/ scaffold | ui/package.json, ui/vite.config.ts, ui/tsconfig.json, ui/index.html, ui/src/main.tsx, ui/src/stores/*.ts, ui/src/App.tsx (shell), ui/src/components/*.tsx (placeholders) |
| 3 | Layer 3 — ui/ components | ui/src/components/Sidebar.tsx, ui/src/components/Board.tsx, ui/src/App.tsx (Go/Pause wiring) |
| 4 | Layer 2 + Layer 3 | server/main.py (POST /api/chat), ui/src/components/ChatPanel.tsx |
| 5 | Layer 1 + Layer 2 + infra | engine_cli/__main__.py, server/run.py, server/main.py (static mount), pyproject.toml |

---

## Review checklist (use before merging each conversation)

- [ ] No `import` of engine internals (`orchestrator`, `runners`, `team_flow`) anywhere in `server/`.
- [ ] No Python imports anywhere in `ui/src/`.
- [ ] All `/api/*` routes are defined **before** the `StaticFiles` mount in `main.py`.
- [ ] `watcher.py` does not raise on missing file or malformed JSON line.
- [ ] `run.py` checks port availability before starting uvicorn and exits with code 1 (not a traceback) if the port is taken.
- [ ] `POST /api/chat` returns HTTP 503 (not 500) when `ANTHROPIC_API_KEY` is absent.
- [ ] `GET /api/files/{filename}` rejects filenames containing `/` or `..` with HTTP 400.
- [ ] The `server` subcommand in `engine_cli/__main__.py` is the only change to existing engine files.
