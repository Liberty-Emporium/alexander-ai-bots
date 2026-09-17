# Updating from OpenBot

Alexander AI Bots follows upstream OpenBot **one week behind**. This is deliberate: a fresh
upstream image can move things the branding layer depends on, and a week of running it on a
live deployment catches that before customers see it.

## The week, in practice

| Day | What happens |
|---|---|
| 0 | OpenBot publishes an update. Pull the new image into a test deployment. |
| 0–6 | Run the test deployment. Check the branding, the vault, the graph, the Help page and the key form. |
| 7 | Publish our release with any branding fixes, and roll it to live deployments. |

## What to check after a new image

The branding layer makes a small number of assumptions about the compiled app. After an update,
walk this list on the **test** deployment:

1. **The product name** — does the app still show your brand, or did upstream change how it is
   set? Re-run `branding/patch-app-bundle.py` against the new bundle.
2. **The sidebar links** — Obsidian Graph, Obsidian Vault, OpenRouter, Help still present and
   in order? The patch script adds them; if upstream changed the sidebar markup, the script
   will say which anchor it could not find.
3. **The asset filename** — the bundle is named with a content hash
   (`index-<hash>.js`). If the hash changed, update the mount in `deploy/docker-run.example.sh`
   and the `<script src>` in `branding/index.html` (the patch script leaves a `?v=` cache-buster).
4. **The vault pages and graph** — regenerate with `vault/build-vault-site.py`; open the graph
   and click a dot.
5. **The Help pages and the key form** — save a key on the test deployment and confirm the
   container restarts and the model line updates.
6. **The login gate** — confirm the app is still behind it (or still open, if that is what you
   configured).

## Pulling a new image

```bash
docker pull ghcr.io/copilotkit/openbot:latest

# copy the shell and bundle out of the NEW image
docker run --rm --entrypoint sh ghcr.io/copilotkit/openbot:latest -c \
  'cat /app/app/dist/index.html' > /tmp/new-index.html
docker run --rm --entrypoint sh ghcr.io/copilotkit/openbot:latest -c \
  'cat /app/app/dist/assets/index-*.js' > /tmp/new-bundle.js

# re-apply the branding
python3 branding/patch-app-bundle.py \
  --bundle /tmp/new-bundle.js --html /tmp/new-index.html \
  --brand "Your Brand" --vault https://vault.example.com/mybots/ \
  --graph https://vault.example.com/mybots/graph.html
```

Then recreate the container with the new image and the re-branded files.

## If something breaks

- The patch script prints a line for every anchor it cannot find — that is the fastest signal
  that upstream moved something.
- The app itself is upstream's; if a bot misbehaves after an update, check OpenBot's release
  notes and issues before changing anything here.
- Keep the previous image tag around (`:v0.0.9` style tags exist upstream) so a rollback is
  one `docker run` away.
