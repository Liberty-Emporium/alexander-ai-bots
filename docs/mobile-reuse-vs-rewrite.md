# Mobile: reuse vs rewrite

Filled in from the real system (OpenBot v0.0.12, four live deployments), not from assumptions.

| Existing component | Reuse | Adapt | Rewrite | Reason |
|---|---|---|---|---|
| Bot engine / gateway | ✓ | | | It is the product. Mobile is a client. |
| Server API (`/api/...`) | ✓ | | | Already the only sanctioned path, with policy and audit. |
| Authentication (better-auth) | ✓ | ✓ | | Single-user deployments need no in-app login; multi-user needs the SSO/session path on a device. |
| Postgres, threads, memory | ✓ | | | Server-side only; the client never touches them. |
| CopilotKit chat runtime | ✓ | ✓ | | Same SSE protocol; a native client must implement the client half. |
| Channel events (SSE) | ✓ | | | Already the realtime feed for activity. |
| Audit trail | ✓ | ✓ | | Reuse as the Activity source; adapt the presentation. |
| Computer control endpoints | ✓ | ✓ | | Reuse wholesale; adapt the touch UI (take/release the wheel). |
| Skills, routines, plugins | ✓ | ✓ | | REST already; expose a subset on mobile. |
| Tenant package (bots) | ✓ | | | One set of bots for both clients. |
| Branding (colours, artwork, favicon, cards) | ✓ | ✓ | | Same identity; different layout rules. |
| Desktop navigation (3-column shell) | | | ✓ | Wrong information hierarchy for a phone. |
| Desktop layouts (workspace, admin) | | | ✓ | Full workspace stays on the desktop. |
| Vault pages + graph | ✓ | ✓ | | Already responsive and touch-enabled; can be linked from mobile. |
| Help pages | ✓ | | | Already mobile-optimised. |
| API types (TypeScript) | ✓ | ✓ | | Read from server source; share what is stable. |
| Push notifications | | | ✗ new | Does not exist anywhere in OpenBot. New backend work. |
| Web app manifest / service worker | | | ✗ new | Absent today; small addition. |

## Three routes, in order of effort

### Route 1 — Installable web app (hours)

Add a web app manifest, icons and a minimal service worker to the branded shell. The apps are
already mobile-optimised, so this yields: home-screen icon, full-screen launch, no browser
chrome — on both iOS and Android, with **zero backend change**.

Good for: everyone today, including the four live customer deployments.

### Route 2 — Capacitor shell (about a day)

Wrap the existing app in a native shell. Reuses 100% of the UI and the whole API. Needs:
secure storage for gate credentials (if the deployment is gated), a splash screen, and store
signing. Still no backend change.

Good for: App Store / Play Store presence quickly, with the current experience.

### Route 3 — Expo / React Native client (weeks)

A genuinely native client. The work is not the bot engine — it is these five things:

1. **Auth** — session cookie (multi-user) or gate credentials (single-user), in secure storage.
2. **Chat** — implement the client half of the CopilotKit runtime protocol over SSE at
   `/api/copilotkit`, plus thread minting at `/api/threads/mint`.
3. **Realtime** — subscribe to `/api/channels/events` (SSE) for channel and bot state.
4. **Computer** — poll `/api/computers/:botId/screenshot` for the live view, and drive
   `control/take` / `control/release` plus the `human/*` inputs for the wheel.
5. **Notifications** — new backend work: a device registry and an APNs/FCM sender fed by the
   events that already exist (a bot asking for help, a routine finishing, a failed turn).

Everything else (bots list, activity, files, skills) is plain REST already.

## Recommendation

Do **Route 1 now** — it is small, it benefits the four live deployments immediately, and it makes
the platform genuinely app-like on a phone this week.

Then choose between Route 2 and Route 3 based on what you want the phone to feel like:
Route 2 is the current product in an app; Route 3 is a purpose-built pocket interface. Both talk
to the same backend, and neither requires touching the bot engine.

## What mobile must never do

- Talk to the computer service, the supervisor, Postgres, or any internal port directly.
- Bypass the gateway, policy or audit for any action.
- Carry server secrets, model keys or MCP credentials in the app bundle.
