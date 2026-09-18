# Cookie gate

A one-password sign-in that issues a **server-signed session cookie**, used instead of HTTP Basic.

## Why not HTTP Basic

Basic credentials are cached by the *browser context* that received the challenge. An installed PWA
runs in its own context (Android WebAPK) or its own container (iOS home-screen web app), so it is
challenged again on every launch. A cookie belongs to the app's own cookie jar and simply persists.
See `docs/mobile-auth-findings.md` for the full investigation.

## How it works

```
phone ──► Caddy ──forward_auth──► gate service (:9091) ──► 204, or 302 to /login
            │
            └──► app (only when the gate answered 204)
```

- `GET /login` serves a branded, mobile-friendly password page
- `POST /login` verifies the password (scrypt) and sets `ob_gate`:
  `HttpOnly; Secure; SameSite=Lax; Max-Age=30 days`
- `GET /verify` is what Caddy asks on every request; a valid cookie answers `204`
- `GET /logout` clears it
- Ten wrong attempts from one address in fifteen minutes are refused

The cookie is `instance:expiry:hmac(instance:expiry, secret)`. Changing the password (or the
secret) invalidates every existing session for that deployment — that is "sign out everywhere".

## Adding a deployment

```bash
# 1. set its password (writes ~/.config/openbot-gate/<instance>.json, mode 600)
python3 gate/gate-set-password.py --instance mybots --name "My Brand" --password '...'

# 2. run the service (a user service; see deploy/ for a unit example)
python3 gate/gate-service.py

# 3. point the site at it: Caddy's forward_auth, as in deploy/Caddyfile.example
```

## Notes

- Nothing is stored on the client but the cookie; the password is typed once and exchanged.
- The password never reaches the app; the gate answers before anything is proxied.
- Rotating the secret signs everyone out. Keeping it (`--keep-secret`) changes the password
  without ending existing sessions.
- WebSockets work: the handshake carries cookies, and `forward_auth` authorises it like any other
  request (verified for the channel-events and live-screen sockets).
- To roll back to HTTP Basic, restore the `basic_auth` block in the Caddyfile — the gate is an
  addition in front of the app, not a change to it.
