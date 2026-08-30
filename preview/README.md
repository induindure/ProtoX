# ProtoPreview

A new shared service for ProtoX that lets the user see a **live, running demo**
of the app ProtoCode just generated for them — a real iframe of a real dev
server, not a code viewer.

## Why a separate service (matches your existing architecture)

ProtoCode (8001/5174) and ProtoTest (8002/5175) are already separate
FastAPI + Vite/React pairs that hand projects to each other over HTTP using
an in-memory `project_store` + `?id=` URL param. ProtoPreview (8003/5176)
follows the exact same pattern, so it drops in without touching how
ProtoCode or ProtoTest work internally.

```
ProtoCode (5174) --"Preview App"--> ProtoPreview backend (8003) --stores files-->
                                     ProtoPreview frontend (5176) opens with ?id=...
                                     --> backend builds project on disk
                                     --> spawns frontend dev server + backend dev server
                                     --> iframe shows the running frontend
```

## What's different from ProtoTest under the hood

ProtoTest writes files to a **tempfile that gets deleted** right after the
test run. ProtoPreview writes files to a **stable folder per project_id**
(`backend/workspaces/<project_id>/`) because the dev servers need to keep
running while the user is looking at the iframe — the folder is only cleaned
up when they hit "Stop preview".

ProtoTest's `stack_runner.py` only had to pick pytest vs jest. ProtoPreview's
`stack_launcher.py` needs a real install+run command for all 7 combos:

| Frontend | Backend       | Frontend command                          | Backend command                        |
|----------|---------------|--------------------------------------------|------------------------------------------|
| React    | FastAPI       | `npm run dev -- --port P --host 0.0.0.0`   | `uvicorn main:app --port P`             |
| React    | Node/Express  | same                                       | `npm run dev` / `node server.js`        |
| React    | Django        | same                                       | `python manage.py runserver 0.0.0.0:P`  |
| Vue      | FastAPI       | same as React (also Vite)                  | same                                    |
| Vue      | Node/Express  | same                                       | same                                    |
| Next.js  | FastAPI       | `npm run dev -- -p P -H 0.0.0.0`            | same                                    |
| Next.js  | Node/Express  | same                                       | same                                    |

The backend dev server's port is picked first, then passed to the frontend
as `VITE_API_URL` / `NEXT_PUBLIC_API_URL` / `REACT_APP_API_URL` env vars, so
generated frontend code that reads `import.meta.env.VITE_API_URL` (a common
convention) can find its backend automatically. This is best-effort — if the
LLM generated a frontend that hardcodes `localhost:8000`, that call will
still hit the *ProtoCode-idea's* imagined port, not the real one. Flag this
as a known limitation for the demo, or note it in your writeup as a "future
work" item — fixing it fully would mean post-processing the generated
frontend code to rewrite its API base URL, which is a bigger change.

## Setup

```bash
# Backend
cd protopreview/backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python app/main.py          # runs on :8003

# Frontend
cd protopreview/frontend
npm install
npm run dev                 # runs on :5176
```

## Wiring into ProtoCode

Apply `protocode_patch.md` — it's a copy-paste addition of one handler
function and one button, following the exact shape of your existing
`handleSendToProtoTest`.

## Known limitations (worth mentioning in your report)

1. **No sandboxing** — generated code runs as real subprocesses on your
   machine (same trust model ProtoTest already uses for running tests).
   Fine for a capstone demo on your own machine; would need Docker
   containers per project before ever exposing this publicly.
2. **No process TTL/cleanup** — if a user never clicks "Stop preview", the
   dev servers keep running. For the demo this is fine; a production version
   would want an idle-timeout reaper similar to `project_store`'s TTL.
3. **npm install runs on every start** — no caching between preview
   sessions. Fine for small generated projects; would want a shared
   `node_modules` cache for anything bigger.
4. **Backend API URL env vars are best-effort** (see above) — only works if
   the generated frontend reads the conventional env var for its framework.
