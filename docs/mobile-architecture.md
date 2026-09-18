# Mobile architecture report

Analysis of the running platform, produced **before** any mobile code is written.
Everything here was read from the live deployment, not guessed.

## What is actually running

| | |
|---|---|
| Engine | **OpenBot v0.0.12** (upstream tag `v0.0.12`, published 2026-09-15) |
| Image | `ghcr.io/copilotkit/openbot@sha256:89d5f76326d06003138561c589b1ff45173852c44896e31ade6e5c4248a936f4` |
| Built | 2026-09-15 |
| Upstream | https://github.com/CopilotKit/OpenBot (MIT) |

The full source of what we run is readable on the deployment machine:

- server source — `/app/server/src` inside the container
- built frontend — `/app/app/dist`
- bot computer — `/app/agent-computer/src`
- tenant package (our bots) — mounted at `/tenant`

No ZIP or extra checkout is needed to map the API; the source is already present.

## Component map

```
                    Alexander AI deployment (one container per customer)
                    ─────────────────────────────────────────────────
  browser ──► Caddy (username/password gate) ──► server (Hono on Bun, :3001)
                                                   │
                                                   ├── app: React/Vite SPA (built, branded by us)
                                                   ├── Postgres (its own volume)
                                                   ├── CopilotKit Intelligence (durable threads/memory)
                                                   └── gateway ──► agent-computer (:4100, loopback, token)
                                                                     Playwright + Chromium (headed, Xvfb)
```

Four deployments run this shape today: Alexander, Randy, State Electric, Davis Carpet.
Each is isolated: own container, database, browser profiles, vault, `.env`.

## Frontend

- React + Vite, compiled to a single bundle (`/app/app/dist/assets/index-<hash>.js`).
- Branding is applied by patching that bundle and the page shell — see `branding/`.
- It is **already mobile-usable**: phone type scale, the nav toggle moved to the bottom for
  thumbs, touch support in the vault graph, no horizontal overflow on any page.
- It is **not installable** as an app: no web app manifest, no service worker.

## Backend

- **Hono** on **Bun**, listening on 3001, serving both the API and the built app.
- Route modules mounted under `/api/...` (full list in `docs/mobile-api-map.md`).
- **Chat** runs through the CopilotKit runtime at `/api/copilotkit` and streams with
  **Server-Sent Events** (`text/event-stream`).
- **Live channel updates** are pushed over SSE at `/api/channels/events`.
- **Durable threads and memory** come from CopilotKit Intelligence; the deployment mints thread
  ids at `/api/threads/mint` and stamps them with a deployment id.

## Authentication

- **better-auth** with session cookies, plus optional SSO (Google, Microsoft, Okta, SAML/OIDC).
- Our four deployments run **single-user mode**: there is no in-app login, every request is
  treated as one administrator, and the public entry point is the **Caddy username/password
  gate** in front of the app (Randy and Davis are deliberately open, with no gate).
- A mobile client therefore has two options: carry the same session cookie (if a real provider
  is configured), or sit behind the same gate credentials for single-user deployments.

## The bot computer, and the one rule that matters

Each bot has a real Chromium on a virtual display. It is reachable **only through the server's
gateway** at `/api/computers/:botId/...`:

- viewing — `status`, `screenshot`, `read`, `page-frame/:toolCallId`
- acting — `navigate`, `snapshot`, `click`, `type`, `key`, `scroll`
- the wheel — `control`, `control/request`, `control/take`, `control/release`, `control/secret`
- human input — `human/secret`, `human/:kind`
- files — `files/list`, `files/read`, `files/write`, `exec`

The computer service itself binds to loopback with its own token and must stay private.
**A mobile client must never talk to it directly**; that would bypass policy, audit and the
hand-over model. This is the existing security boundary and mobile does not get an exception.

## Memory, files, skills, routines, governance

- **Memory** — per-channel durable threads (Intelligence) plus the bot's Obsidian vault, mounted
  from a host folder, with generated pages and an interactive graph.
- **Files** — the vault *is* the bot's workspace; the same file endpoints above read and write it.
- **Skills** — `/api/plugins/skills`; **routines** — `/api/routines`.
- **Governance** — every action is decided by policy before it happens and recorded afterwards;
  the trail is readable at `/api/admin/audit-events` and is append-only by design.

## What mobile needs that does not exist yet

1. **Push notifications.** OpenBot has no APNs/FCM path. The *events* exist (a bot asking for
   help, a routine finishing, a turn failing) but nothing forwards them to a device. This is new
   work in the backend, and the only item here that is.
2. **A mobile auth story for real (multi-user) deployments.** Single-user mode plus a gate is
   fine for the four current sites; a store-distributed app would want the SSO path.
3. **Installability.** A manifest and service worker (or a native shell) so the app can live on a
   home screen and open full-screen.

## Constraints carried into any mobile work

- Do not modify the bot engine; mobile is a client of it.
- Do not break the desktop app; it is the full workspace.
- Keep TypeScript strict; keep secrets out of the app bundle.
- The desktop stays the admin surface (policy, plugins, people, audit, computers).
