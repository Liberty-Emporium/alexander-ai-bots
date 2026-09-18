# Installable on a phone (PWA)

Turns a deployment into an app that can be added to a home screen and opened full-screen, on
iPhone and Android, with **no container rebuild and no database change**.

`build-pwa.py` writes the assets; the reverse proxy serves them; the app's page shell links them.

## What it writes

| File | Purpose |
|---|---|
| `manifest.webmanifest` | name, icons, `display: standalone` |
| `sw.js` | a **pass-through** service worker — it caches nothing |
| `pwa-icon-192.png`, `pwa-icon-512.png` | home-screen icons |
| `apple-touch-icon.png` | iOS home-screen icon |

## Why the service worker caches nothing

A caching service worker is the classic way to ship stale app code and stale API responses to a
phone. This one exists only because installability requires it: every request goes to the
network, unchanged. Nothing can be served from a cache that does not exist.

## How it is wired

1. Assets live on the host (for example `/home/you/pwa-site/<slug>/`).
2. The reverse proxy serves four paths from that folder — `/manifest.webmanifest`, `/sw.js`,
   `/pwa-icon-192.png`, `/pwa-icon-512.png` — with the right content types (see the Caddy block
   `build-pwa.py` prints).
3. The app's page shell carries the manifest link, the theme colour, the iOS meta tags and the
   service-worker registration.

Steps 2 and 3 never touch the app container: the page shell is already a bind-mounted file, and
the proxy is a host process. That is the safe way to add this — recreating a container to add
files is where a mistyped volume flag can re-initialise a database.

## Installing it

- **Android / Chrome** — open the site, menu → *Install app* (or the install icon in the address bar).
- **iPhone / Safari** — *Share* → *Add to Home Screen*.

## Things worth knowing

- **A gated deployment may ask for the password again** when launched from the home screen:
  basic-auth credentials are not reliably persisted in standalone mode. Deployments with no gate
  (open) do not have this issue.
- **Push notifications** are not part of this. iOS also requires 16.4+ and an installed PWA
  before it will deliver any. The backend side does not exist yet either — see
  `docs/mobile-architecture.md`.
- **Verify with the row counts, not by eye.** If you ever do recreate a container, compare the
  data first and after (the deployments' tables are listed in `docs/mobile-api-map.md`).
