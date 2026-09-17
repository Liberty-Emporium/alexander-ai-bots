# The key service

`save-key-service.py` is the small endpoint behind the Help page's OpenRouter form:

- `POST /save-key` writes `OPENAI_API_KEY` into that deployment's `.env` and restarts it
- `GET /info` reports the model the agents run on and whether a key is set

It listens on `127.0.0.1:9090` only, and every request must carry the shared secret that Caddy
adds — so it is not reachable except through the login gate. The secret is generated on first
run at `~/.config/openbot-save-key.secret`; put the same value in the Caddyfile.

Add one entry per deployment to `INSTANCES`, then run it as a user service.
