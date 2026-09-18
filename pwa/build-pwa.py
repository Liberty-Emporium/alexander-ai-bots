#!/usr/bin/env python3
"""Make a deployment installable on a phone (PWA assets).

Writes, for one deployment:
  manifest.webmanifest   name, icons, standalone display
  sw.js                  a pass-through service worker (caches NOTHING)
  pwa-icon-192.png       home-screen icon
  pwa-icon-512.png
  apple-touch-icon.png

Nothing here touches the app container, its volumes, or its database: the files
are served by the reverse proxy from the host, and the app's page shell links
them. That is deliberate - adding files the "normal" way (recreating the
container) is how a database gets re-initialised by a typo.

Usage:
  build-pwa.py --slug mybots --name "My Brand" --logo logo.png --out /home/you/pwa-site/mybots
"""
import argparse
import json
import pathlib

SW = """/* Minimal service worker for installability.
 *
 * Deliberately does NO caching: every request goes to the network, so this can
 * never serve stale app code or a stale API response.
 */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {
  /* network only - no respondWith() */
});
"""

HEAD_TAGS = """    <link rel="manifest" href="/manifest.webmanifest" />
    <meta name="theme-color" content="#041027" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    <meta name="apple-mobile-web-app-title" content="{name}" />
    <script>
      if ("serviceWorker" in navigator) {{
        addEventListener("load", function () {{
          navigator.serviceWorker.register("/sw.js").catch(function () {{}});
        }});
      }}
    </script>
"""

CADDY_ROUTES = """\thandle /manifest.webmanifest {{
\t\theader Content-Type application/manifest+json
\t\troot * {out}
\t\tfile_server
\t}}
\thandle /sw.js {{
\t\theader Content-Type application/javascript
\t\theader Cache-Control no-cache
\t\troot * {out}
\t\tfile_server
\t}}
\thandle /pwa-icon-192.png {{
\t\troot * {out}
\t\tfile_server
\t}}
\thandle /pwa-icon-512.png {{
\t\troot * {out}
\t\tfile_server
\t}}
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--short", default=None)
    ap.add_argument("--logo", required=True, help="square PNG of the logo")
    ap.add_argument("--out", required=True, help="directory to write into")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    from PIL import Image  # imported here so --help works without Pillow

    logo = Image.open(args.logo).convert("RGBA")
    logo.resize((512, 512), Image.LANCZOS).save(out / "pwa-icon-512.png")
    logo.resize((192, 192), Image.LANCZOS).save(out / "pwa-icon-192.png")
    logo.resize((180, 180), Image.LANCZOS).save(out / "apple-touch-icon.png")

    manifest = {
        "name": args.name,
        "short_name": args.short or args.name,
        "description": f"{args.name} - private AI coworkers with their own computers.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait-primary",
        "background_color": "#041027",
        "theme_color": "#041027",
        "icons": [
            {"src": "/pwa-icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/pwa-icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    (out / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "sw.js").write_text(SW)

    print(f"wrote PWA assets to {out}")
    print()
    print("1. Serve them from the reverse proxy (one block per deployment):")
    print(CADDY_ROUTES.format(out=out))
    print("2. Put these tags in the app's page shell, before </head>:")
    print(HEAD_TAGS.format(name=args.name))
    print("3. Reload on a phone: Chrome shows Install; Safari uses Share > Add to Home Screen.")


if __name__ == "__main__":
    main()
