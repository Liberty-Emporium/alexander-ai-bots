# Mobile auth findings

Why the installed apps sometimes ask for the password again, what it means, and the smallest
safe way to fix it. **Investigation only — nothing here has been changed.**

## Current authentication architecture

```
phone / desktop
      │  HTTPS
      ▼
   Caddy                     ← the gate: HTTP Basic (WWW-Authenticate: Basic realm="restricted")
      │
      ▼
   Hono server (:3001)       ← single-user mode: every request is one administrator, no in-app login
      │
      ▼
   gateway → bot computer
```

Verified on the live deployments:

- The gate answers `401` with `www-authenticate: Basic realm="restricted"` and nothing else.
- **The application sets no cookie at all** — not on the page, not on `/api/me`, on a gated
  deployment or an open one. Single-user mode issues no session.
- Therefore the *only* thing remembering a password is the browser's HTTP Basic credential
  cache. There is no session, no token, no cookie to persist.

That last point is the whole explanation.

## Why standalone mode behaves differently

HTTP Basic credentials are cached by the **browser context** that received the challenge. A
PWA launched from a home screen is *not* that context:

- **Android** — an installed PWA runs as a WebAPK: its own task, its own cookie jar and its own
  HTTP auth cache. Chrome's cached Basic credentials are not shared with it, so the first request
  of a launch is unauthenticated and the app is challenged again.
- **iOS** — a home-screen web app runs in its own container with storage isolated from Safari
  (cookies, localStorage and the credential cache are separate). Safari's saved password does not
  carry over, and iOS does not offer Keychain autofill inside the standalone container the way it
  does in Safari.

In both cases the app is *correctly* challenged — the gate is doing its job. The problem is that
HTTP Basic has no persistent state to carry across contexts, so every launch starts over.

*Locally verified:* the challenge, the absence of any cookie, and that both WebSocket endpoints
upgrade through the gate. *Platform behaviour above is documented by Apple and Google; it was not
tested on physical devices from this machine.*

## Per-deployment behaviour

| Deployment | Gate | Expected installed-app behaviour |
|---|---|---|
| Alexander AI Bot | Basic, `Alexander.ai` | challenges on each launch from the home screen |
| State Electric | Basic, `john` | challenges on each launch |
| Randy AI Bot | none (open) | no prompt; nothing to persist |
| Davis Carpet | none (open) | no prompt |

So it is not a bug in any one deployment: it is the two gated ones behaving exactly as HTTP
Basic does in a separate app context.

## Security implications

- **Do not** try to fix this by storing the password in the client — in `localStorage`, in a
  cache, or anywhere else. That would put a credential with full administrative access into
  storage that any script on the page can read.
- **Do not** remove the gate to make the prompt go away. Randy and Davis are open *by choice*;
  Alexander and State are gated *by choice*, and removing the gate would expose the platform's
  administration and its bots' connected accounts.
- **Do not** fake a client-side login. The gate is the security boundary; a client-side stand-in
  would be a lock drawn on a picture of a door.
- The correct shape is a **session that belongs to the server**: the server issues something
  after a successful sign-in, and the client presents it. That is the only thing that survives a
  standalone launch *and* remains revocable.

## Possible solutions, smallest first

| Option | What it is | Effort | Keeps the boundary? |
|---|---|---|---|
| **Cookie-based gate** | Replace HTTP Basic with a small login page that sets a signed, expiring session cookie (one shared password, same as today). Cookies persist in the standalone app's own jar, so a launch does not re-prompt. | Small — one Caddy-level service, the pattern already used by `services/save-key-service.py` | Yes — same single credential, server-issued, revocable, HttpOnly + Secure |
| **Real sign-in (better-auth)** | Configure an identity provider (Google/Microsoft/Okta) and let the app's own session cookie carry it. | Medium — provider setup per deployment | Yes — and adds per-person identity, 2FA, revocation |
| **Native credential storage** | Store the gate credential in iOS Keychain / Android Keystore in a native shell. | Medium (needs Capacitor/Expo) | Only if done carefully — the credential still exists on the device |
| **Do nothing** | Accept a password prompt on launch for the two gated apps. | None | Yes |

The native option is the weakest of the four for the least benefit: it adds a shell and puts a
full-admin credential on the device, to solve a problem a cookie solves without either.

## Recommended next step

1. **Leave all four deployments exactly as they are** until you decide. The prompt is an
   annoyance, not a defect, and nothing is exposed by it.
2. If the prompt is worth removing, do the **cookie-based gate** first: it is the smallest change
   that survives a standalone launch, keeps the same single credential, and stays server-issued
   and revocable. It can be built and tested on one deployment before touching the others.
3. Only if you want per-person identity (Randy and John signing in as themselves) is
   **better-auth with a provider** the right move — and that is a product decision, not a mobile
   one.
