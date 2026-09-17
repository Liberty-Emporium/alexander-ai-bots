# Branding this platform for a customer

This platform is white-label. The branding layer is small and separate from the engine, so a
customer deployment is the same software with different names, colours, artwork and domains.

## What changes for a customer

| Thing | How it changes |
|---|---|
| Name of the app | `branding/patch-app-bundle.py --brand "Customer Name"` |
| Sidebar links | same script: vault, graph, OpenRouter, Help URLs |
| Background artwork | `branding/assets/hero.png` |
| Tab icon | `branding/assets/favicon.png`, `favicon-32.png`, `apple-touch-icon.png` |
| Explore-agent cards | `branding/assets/card-1.png` … `card-4.png` |
| Domain | `deploy/cloudflared-config.example.yml` and the Caddyfile site block |
| Login | one `basic_auth` entry in `deploy/Caddyfile.example` |
| Bots and channels | `tenant-package/agents.yaml`, `channels.yaml` |
| Model | `tenant-package/model.yaml`, `OPENAI_API_KEY` in `.env` |
| Help pages | `help/build-help-pages.py` (names, URLs, the `.env` it points at) |
| Vault pages and graph | `vault/build-vault-site.py` |

## What stays the same

The engine — OpenBot's agent platform, the governed action gateway, the policy engine, skills,
routines, the per-bot computer, and the audit trail. That is deliberate: the safety and
governance of the platform is not something branding should touch.

## A customer deployment in eight steps

1. Create a folder for the deployment, copy `deploy/.env.example` to `.env`, fill in the keys.
2. Copy `tenant-package/` into the deployment folder and edit the bots, channels and model.
3. Copy `deploy/migrate.sh` into the deployment folder.
4. Put the customer's artwork in `branding/assets/`, then brand the shell and bundle:
   `python3 branding/patch-app-bundle.py --bundle … --html … --brand "Customer" --vault … --graph …`
5. Start it: `deploy/docker-run.example.sh customer-bots 3002 /home/you/customer-bots`
6. Add a Caddy site block for the customer's domain with their own username and password.
7. Point their domain at the tunnel.
8. Generate their Help and vault pages with their URLs, and run the refresh timers.

## What a customer needs to know

- Their bots think with **their own OpenRouter key** (the Help page's form saves it).
- Their vault is **theirs**: a folder of Markdown notes on the machine, readable in Obsidian.
- Logins they perform stay in **their** bot's browser — passwords are never given to a bot.
- Every action their bots take is **recorded** and reviewable.

## Keeping customers separate

Each deployment has its own container, database, browser profiles, vault folder and `.env`.
Never point two deployments at the same database or the same profile volume — that is the
boundary that keeps one customer's logins and files out of another's.
