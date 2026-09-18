# Mobile capability gap: PWA vs native

What the installed PWA can already do, measured on the live deployments, and what — if anything —
genuinely requires a native app.

Tested in a phone-emulated browser (390×844, touch enabled) against the running deployments, with
**all write requests blocked** so the checks could not change any data.

## The table

| Capability | PWA status | Native required? | Notes |
|---|---|---|---|
| Chat | **works** | no | CopilotKit runtime at `/api/copilotkit`; `GET /api/copilotkit/info` reports `transport.streaming: true` |
| Streaming responses | **works** | no | the runtime streams; a pass-through service worker does not buffer it |
| Bot status | **works** | no | `GET /api/agents`, `/api/computers/:botId/status` |
| Channel events | **works** | no | **WebSocket** at `/api/channels/events` — verified upgrading through the gate and tunnel |
| Computer view (live screen) | **works** | no | **WebSocket** at `/api/computers/:botId/stream` — verified upgrading; renders inline as a 333×208 preview, full-screen on tap (390×844) |
| Computer control (take the wheel) | **works, but cramped** | no | a **Take control** button exists and functions; measured **101×34 px**, and every icon button is **27–40 px** — below the 44 px touch minimum |
| Files | **works** | no | `/api/computers/:botId/files/*` |
| Activity | **works** | no | the audit trail, `/api/admin/audit-events` |
| Authentication | **weak in standalone** | no | see `docs/mobile-auth-findings.md` — HTTP Basic cannot persist across app contexts; a cookie-based gate fixes it without native |
| Push notifications | **possible, not built** | **no** | Web Push works on Android and on iOS 16.4+ for an **installed** PWA. Requires new backend work (subscriptions + VAPID/APNs), not a native app |
| Background notifications | **possible, not built** | no | same mechanism as push; the events already exist server-side |
| Camera | **works** | no | `getUserMedia` in an installed PWA, with permission |
| Microphone | **works** | no | `getUserMedia`; needed for voice input later |
| Biometrics (app lock) | **works** | no | WebAuthn platform authenticator (Face ID / Touch ID / Android biometrics) |
| Deep links (open a specific bot) | **partial** | partly | Android supports protocol handlers in the manifest; iOS support for PWA deep links is limited. A native shell is better here |
| App-store distribution | **not possible** | **yes** | a PWA cannot be listed in the App Store or Play Store; Capacitor or Bubblewrap can wrap the same app |
| Offline behaviour | **none today** | no | the service worker deliberately caches nothing. Read-only caching could be added if wanted; the bots need the network regardless |

## What this means

**Only two things genuinely require leaving the PWA behind:** app-store distribution, and (partly)
deep links. Everything else — including push notifications, camera, microphone and biometrics — is
achievable in the installed PWA, because Web Push and WebAuthn both work in installed PWAs on
current iOS and Android.

**The two real problems are fixable in the web app, not by rewriting it:**

1. **Touch targets.** Every icon button on a phone measures 27–40 px; Apple's minimum is 44 px.
   `Take control` is 34 px tall. This is a CSS pass of the same kind already done for the rest of
   mobile — no native code involved.
2. **The auth prompt on gated deployments.** A cookie-based gate (one shared password, a
   server-issued session cookie) removes it without weakening anything. Details in
   `docs/mobile-auth-findings.md`.

## The deciding question: is computer control good on a phone?

Measured, not assumed:

- The live screen **does** work on a phone — it opens inline (333×208) and goes **full-screen**
  (390×844) on tap, streamed over a WebSocket that upgrades cleanly through the gate and the
  tunnel.
- **Take control is present and reachable**, and the full-screen view is the right shape for a
  phone (the bot's screen owns the display while you drive it).
- What is wrong is only the sizing: 34 px buttons, and no obvious affordance that the screen is
  interactive once you have the wheel.

So the distinctive feature of the platform — a bot that works a computer, and a human who can take
it over — is **usable on a phone today**, and becomes comfortable with a touch-target pass. It does
not by itself justify a native rewrite.

## Recommendation

**Stay PWA.** Do these in order:

1. **Touch-target pass** — bring every icon button and the Take control control to ≥44 px on small
   screens. Small, contained, and it improves all four deployments immediately.
2. **Cookie-based gate** — only if the launch prompt bothers you; smallest safe change, per the
   auth findings.
3. **Push notifications** — when you want them. Web Push, fed by the events that already exist
   (a bot asking for help, a routine finishing, a failed turn). New backend work, no native app.
4. **Revisit Capacitor/Expo only if** you decide you need App Store / Play Store presence or
   reliable deep links — and if you do, wrap this app rather than rebuild it.
