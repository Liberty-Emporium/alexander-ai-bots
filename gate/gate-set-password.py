#!/usr/bin/env python3
"""Set (or change) the password for one deployment's cookie gate.

    gate-set-password.py --instance alexander --name "Alexander AI Bot" --password 'secret'

Writes ~/.config/openbot-gate/<instance>.json (mode 600) containing a scrypt
hash of the password, the display name for the login page, and a fresh signing
secret. Rotating the secret invalidates every existing session for that
deployment - which is what "sign out everywhere" means here.
"""
import argparse
import hashlib
import json
import os
import pathlib
import secrets

CONF_DIR = pathlib.Path.home() / ".config/openbot-gate"
SCRYPT = dict(n=2 ** 14, r=8, p=1, dklen=32)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True, help="the id Caddy passes as X-Instance")
    ap.add_argument("--name", required=True, help="the name shown on the login page")
    ap.add_argument("--password", required=True)
    ap.add_argument("--days", type=int, default=30, help="how long a sign-in lasts on a device")
    ap.add_argument("--keep-secret", action="store_true", help="keep existing sessions alive")
    args = ap.parse_args()

    CONF_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(CONF_DIR, 0o700)
    path = CONF_DIR / f"{args.instance}.json"

    secret = secrets.token_hex(32)
    if args.keep_secret and path.exists():
        try:
            secret = json.loads(path.read_text()).get("secret", secret)
        except (OSError, json.JSONDecodeError):
            pass

    salt = secrets.token_hex(16)
    conf = {
        "name": args.name,
        "salt": salt,
        "hash": hashlib.scrypt(args.password.encode(), salt=bytes.fromhex(salt), **SCRYPT).hex(),
        "secret": secret,
        "days": args.days,
    }
    path.write_text(json.dumps(conf, indent=2) + "\n")
    os.chmod(path, 0o600)
    print(f"wrote {path}")
    print("restart the gate service if it is already running:  systemctl --user restart openbot-gate.service")


if __name__ == "__main__":
    main()
