# pathly-server — Implementation Plan

**Feature:** pathly-server
**Total conversations:** 5
**Tech stack:** FastAPI + uvicorn + sse-starlette (backend) · React + Vite + Zustand (frontend)

---

## Phasing principle

Each conversation leaves the codebase runnable. Natural seams follow the layer
boundary: API first → state stores → UI components → chat/preview → production wiring.

Each conversation touches at most 5–6 files (per the lesson: if a conversation
touches more than 5 files, split it).

---

## Conv 1 — FastAPI backend + SSE watcher

**Stories:** S8 (backend half)
**Layer:** `pathly-engine/server/`

| # | Task | Files (new/modified) | Purpose |
|---|------|----------------------|---------|
| 1.1 | Create `server/` package | `server/__init__.py` | Package scaffold |
| 1.2 | `GET /api/state` | `server/main.py` | Reads and returns `STATE.json` for the active feature |
| 1.3 | `GET /api/files`, `GET /api/files/{filename}` | `server/main.py` | Lists and serves MD files under `plans/<feature>/` |
| 1.4 | `POST /api/go`, `POST /api/pause` | `server/main.py` | Spawns `pathly go` / `pathly pause` subprocess |
| 1.5 | SSE watcher | `server/watcher.py` | asyncio tail of EVENTS.jsonl; yields new lines to connected clients |
| 1.6 | `GET /api/events` SSE endpoint | `server/main.py` | Streams watcher output to browser |

**Verify:** `uvicorn server.main:app --port 8765` starts; `curl http://localhost:8765/api/state` returns JSON or `{"error": "no active feature"}`.

**Dependencies:** none (no UI yet)

---

## Conv 2 — React scaffold + Zustand stores + SSE hook

**Stories:** S8 (frontend half)
**Layer:** `pathly-engine/ui/`

| # | Task | Files (new/modified) | Purpose |
|---|------|----------------------|---------|
| 2.1 | Vite + React project | `ui/package.json`, `ui/vite.config.ts`, `ui/index.html` | Project scaffold |
| 2.2 | `featureStore` | `ui/src/stores/featureStore.ts` | Holds stage, conversations[], lastEvent, error; connects EventSource |
| 2.3 | `fileStore` | `ui/src/stores/fileStore.ts` | Holds fileList[], selectedFile, fileContent |
| 2.4 | `chatStore` | `ui/src/stores/chatStore.ts` | Holds messages[], streaming bool, pendingAction |
| 2.5 | SSE hook in featureStore | `ui/src/stores/featureStore.ts` | `EventSource` → parses events → updates store; reconnect with back-off |
| 2.6 | Three-column layout shell | `ui/src/App.tsx` | Renders `<Sidebar />`, `<Board />`, `<ChatPanel />` placeholders |

**Verify:** `npm run dev` in `ui/` starts on port 5173; browser shows three empty columns; DevTools Network tab shows open SSE connection to `/api/events`.

**Dependencies:** Conv 1 (SSE endpoint must exist for the EventSource to connect)

---

## Conv 3 — Sidebar + Board components

**Stories:** S2, S3, S6, S7
**Layer:** `pathly-engine/ui/src/components/`

| # | Task | Files (new/modified) | Purpose |
|---|------|----------------------|---------|
| 3.1 | Features section | `ui/src/components/Sidebar.tsx` | Lists feature names; highlights active |
| 3.2 | Files section | `ui/src/components/Sidebar.tsx` | Lists MD files from fileStore; click triggers file load |
| 3.3 | Agents section | `ui/src/components/Sidebar.tsx` | Rows with status dots derived from featureStore.lastEvent.last_actor |
| 3.4 | Kanban columns | `ui/src/components/Board.tsx` | Five columns; highlights active stage from featureStore.stage |
| 3.5 | Conversation cards | `ui/src/components/Board.tsx` | Status icon per card; updates on SSE event |
| 3.6 | Go / Pause header buttons | `ui/src/App.tsx` | POST /api/go and /api/pause; disabled states per story S6 rules |

**Verify:** With the FastAPI server running and a real `STATE.json` present, the board shows the correct highlighted column, conversation cards appear, agent dots reflect `last_actor`.

**Dependencies:** Conv 2 (stores must exist)

---

## Conv 4 — Chat panel + markdown file preview

**Stories:** S4, S5
**Layer:** `pathly-engine/ui/src/components/` + `pathly-engine/server/main.py`

| # | Task | Files (new/modified) | Purpose |
|---|------|----------------------|---------|
| 4.1 | `POST /api/chat` endpoint | `server/main.py` | Accepts `{message, state}`, proxies to Claude API, streams SSE tokens back |
| 4.2 | ChatPanel message list | `ui/src/components/ChatPanel.tsx` | Renders user and assistant messages; streaming tokens append in real time |
| 4.3 | ChatPanel input | `ui/src/components/ChatPanel.tsx` | Text input + send; updates chatStore |
| 4.4 | File preview card | `ui/src/components/ChatPanel.tsx` | Renders fileStore.fileContent as inline markdown card when selectedFile changes |
| 4.5 | "show me X" intent parser | `ui/src/components/ChatPanel.tsx` | If user message matches `show me <filename>`, loads file instead of (or before) calling chat |

**Verify:** Type "show me USER_STORIES.md" → file card renders. Type "what's next?" → streaming Claude response appears token by token.

**Dependencies:** Conv 2 (chatStore, fileStore), Conv 3 (sidebar click sets fileStore.selectedFile)

---

## Conv 5 — Production build + `pathly server` command

**Stories:** S1
**Layer:** `pathly-engine/engine_cli/`, `pathly-engine/server/main.py`, `pathly-engine/pyproject.toml`

| # | Task | Files (new/modified) | Purpose |
|---|------|----------------------|---------|
| 5.1 | `npm run build` output | `ui/dist/` (generated) | Production React bundle |
| 5.2 | FastAPI static file mount | `server/main.py` | `StaticFiles` mount serves `ui/dist/` at `/`; SPA catch-all for React Router |
| 5.3 | `pathly server` subcommand | `engine_cli/__main__.py` | Parses `server` command; calls `server.run` |
| 5.4 | `server/run.py` launcher | `server/run.py` | Starts uvicorn on 8765; opens browser after ready check; handles port-in-use error |
| 5.5 | Dependency additions | `pyproject.toml` | Adds `fastapi`, `uvicorn[standard]`, `sse-starlette`, `anthropic` to `[project.dependencies]` |

**Verify (smoke test):** Run `pathly server` from repo root → browser opens → board shows real data → append a line to EVENTS.jsonl → board updates within 2 seconds → Ctrl+C stops cleanly.

**Dependencies:** Conv 1–4 complete; React build must succeed before FastAPI static mount is useful.
