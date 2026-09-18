#!/usr/bin/env python3
"""Cookie-based gate for the Alexander AI deployments.

Replaces HTTP Basic, which cannot persist across a standalone PWA's app context
(that is why installed apps re-prompt on every launch). Here the password is
typed once, exchanged for a server-signed HttpOnly cookie, and the cookie is
what persists - in the installed app's own cookie jar.

Caddy asks this service before proxying: forward_auth -> GET /verify. A valid
cookie answers 204 and the request continues; anything else answers 302 to the
login page.

Nothing is stored on the client except the cookie, and the cookie is revocable:
change the instance secret (or the password) and every session dies.

Usage:
    gate-set-password.py --instance alexander --name "Alexander AI Bot" --password '...'
    python3 gate-service.py            (listens on 127.0.0.1:9091)

Per-instance state lives in ~/.config/openbot-gate/<instance>.json (mode 600):
    {"name": "...", "salt": "...", "hash": "...", "secret": "...", "days": 30}
"""
import hashlib
import hmac
import json
import os
import pathlib
import secrets
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

CONF_DIR = pathlib.Path.home() / ".config/openbot-gate"
COOKIE = "ob_gate"
DEFAULT_DAYS = 30
SCRYPT = dict(n=2 ** 14, r=8, p=1, dklen=32)


def load(instance: str) -> dict | None:
    path = CONF_DIR / f"{instance}.json"
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def derive(password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    return hashlib.scrypt(password.encode(), salt=salt, **SCRYPT).hex()


def sign(instance: str, expiry: int, secret: str) -> str:
    msg = f"{instance}:{expiry}".encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def make_cookie(instance: str, conf: dict) -> str:
    expiry = int(time.time()) + int(conf.get("days", DEFAULT_DAYS)) * 86400
    return f"{instance}:{expiry}:{sign(instance, expiry, conf['secret'])}"


def cookie_ok(instance: str, conf: dict, raw: str | None) -> bool:
    if not raw:
        return False
    try:
        got_instance, expiry_s, signature = raw.split(":", 2)
        expiry = int(expiry_s)
    except ValueError:
        return False
    if got_instance != instance or expiry < time.time():
        return False
    return hmac.compare_digest(signature, sign(instance, expiry, conf["secret"]))


LOGIN_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in - {name}</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{
    margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
    background: #041027; color: #eaf2ff;
    font: 17px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif;
    padding: 20px;
  }}
  .card {{
    width: 100%; max-width: 380px; border: 1px solid #1d3a6b; border-radius: 18px;
    background: #081831f2; padding: 26px 24px; box-shadow: 0 0 40px rgba(30,90,190,.25);
  }}
  h1 {{ margin: 0 0 4px; font-size: 22px; text-shadow: 0 0 12px rgba(90,170,255,.5); }}
  p.sub {{ margin: 0 0 20px; color: #9fb6d9; font-size: 15px; }}
  label {{ display: block; font-size: 14px; color: #9fb6d9; margin-bottom: 6px; }}
  input[type=password] {{
    width: 100%; padding: 14px 15px; border-radius: 12px; border: 1px solid #2b5390;
    background: #081c3c; color: #eaf2ff; font-size: 17px; box-sizing: border-box;
  }}
  button {{
    margin-top: 16px; width: 100%; padding: 15px; border: 0; border-radius: 12px;
    background: rgb(40,150,255); color: #041027; font-weight: 800; font-size: 17px; cursor: pointer;
  }}
  button:hover {{ background: #59b0ff; }}
  .err {{ margin-top: 14px; color: #ff9b9b; font-weight: 600; }}
  .note {{ margin-top: 18px; color: #6f87ab; font-size: 13px; }}
</style>
</head>
<body>
  <form class="card" method="post" action="/login">
    <h1>{name}</h1>
    <p class="sub">This workspace is private. Enter the password to continue.</p>
    <input type="hidden" name="next" value="{next}">
    <label for="password">Password</label>
    <input id="password" name="password" type="password" autocomplete="current-password" autofocus>
    <button type="submit">Sign in</button>
    {error}
    <p class="note">You will stay signed in on this device for {days} days.</p>
  </form>
</body>
</html>
"""

FAILS: dict[str, list[float]] = {}
WINDOW = 900
MAX_FAILS = 10


def too_many(ip: str) -> bool:
    now = time.time()
    attempts = [t for t in FAILS.get(ip, []) if now - t < WINDOW]
    FAILS[ip] = attempts
    return len(attempts) >= MAX_FAILS


class Handler(BaseHTTPRequestHandler):
    server_version = "openbot-gate"

    def log_message(self, fmt, *args):
        pass

    def _instance(self) -> str:
        return self.headers.get("X-Instance", "").strip()

    def _redirect(self, location: str, cookie: str | None = None) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        if cookie is not None:
            self.send_header(
                "Set-Cookie",
                f"{COOKIE}={cookie}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age={DEFAULT_DAYS * 86400}",
            )
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _html(self, body: str, code: int = 200) -> None:
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _page(self, conf: dict, next_path: str, error: str = "") -> str:
        return LOGIN_PAGE.format(
            name=conf.get("name", "Workspace"),
            next=quote(next_path or "/", safe="/"),
            error=f'<p class="err">{error}</p>' if error else "",
            days=conf.get("days", DEFAULT_DAYS),
        )

    def _cookies(self) -> str | None:
        raw = self.headers.get("Cookie", "")
        for part in raw.split(";"):
            k, _, v = part.strip().partition("=")
            if k == COOKIE:
                return v
        return None

    def do_GET(self) -> None:
        url = urlparse(self.path)
        instance = self._instance()
        conf = load(instance)
        if not conf:
            self._html("This deployment is not configured for the gate.", 503)
            return

        if url.path == "/login":
            next_path = parse_qs(url.query).get("next", ["/"])[0]
            if cookie_ok(instance, conf, self._cookies()):
                self._redirect(next_path or "/")
                return
            self._html(self._page(conf, next_path))
            return

        if url.path == "/verify":
            if cookie_ok(instance, conf, self._cookies()):
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            next_path = self.headers.get("X-Forwarded-Uri", "/")
            self._redirect(f"/login?next={quote(next_path, safe='/')}")
            return

        if url.path == "/logout":
            self.send_response(302)
            self.send_header("Location", "/login")
            self.send_header("Set-Cookie", f"{COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        self._html("Not found.", 404)

    def do_POST(self) -> None:
        url = urlparse(self.path)
        instance = self._instance()
        conf = load(instance)
        if not conf:
            self._html("This deployment is not configured for the gate.", 503)
            return
        if url.path != "/login":
            self._html("Not found.", 404)
            return

        ip = self.client_address[0]
        if too_many(ip):
            self._html(self._page(conf, "/", "Too many attempts. Try again in a few minutes."), 429)
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        form = parse_qs(self.rfile.read(length).decode(errors="replace"))
        password = (form.get("password", [""])[0] or "")
        next_path = (form.get("next", ["/"])[0] or "/")

        if not hmac.compare_digest(derive(password, conf["salt"]), conf["hash"]):
            FAILS.setdefault(ip, []).append(time.time())
            self._html(self._page(conf, next_path, "That password is not correct."), 401)
            return

        FAILS.pop(ip, None)
        self._redirect(next_path or "/", make_cookie(instance, conf))


if __name__ == "__main__":
    CONF_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONF_DIR, 0o700)
    server = ThreadingHTTPServer(("127.0.0.1", 9091), Handler)
    print("gate service on 127.0.0.1:9091")
    server.serve_forever()
