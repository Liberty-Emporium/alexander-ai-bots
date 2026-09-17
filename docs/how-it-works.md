# How it works

A plain-language tour of the platform, and a map of which file does what.

## The shape of it

```
your browser
   │  https
   ▼
Cloudflare tunnel  ──►  Caddy  ──►  the app (one container per deployment)
                          │            ├── the bots (tenant package)
                          │            ├── each bot's virtual computer
                          │            └── its database
                          ├── /help/      generated Help pages
                          ├── /save-key   writes a new OpenRouter key
                          └── vault pages + graph (a second site block)
```

Each deployment is **one container**: its own database, its own browser profiles, its own
vault folder, its own `.env`. Nothing is shared between deployments except the machine.

## The bots

A bot is a set of instructions (`tenant-package/agents.yaml`) plus a model. You talk to it in
a channel; it answers, and when a task needs a website it drives its own browser — navigating,
clicking, typing, reading, saving files.

Every action goes through one gateway that decides it against the deployment's policy and
writes an audit row before it happens. That is why you can always see what was done, and why
a refusal names the rule that refused it.

## The virtual computer and taking the wheel

Each bot has a real browser on a real machine (a headed Chromium on a virtual display — the
stable configuration, and the one that does not announce itself as a robot). When the bot
meets a login or a code, it asks for help. You take the wheel: the bot's screen becomes yours,
you sign in directly on the page, and you hand control back. The bot keeps that signed-in
browser afterwards.

Passwords are typed into the site. The bot never receives them, and they are never stored in
the transcript.

## The Obsidian vault (long-term memory)

Every bot's workspace is a folder of plain Markdown notes — an Obsidian vault:

- the bot reads it before answering questions about your past work
- the bot writes notes into it as it learns and finishes things
- two records are written automatically: **Activity Log** (every action, from the audit trail)
  and **Conversations** (each channel's latest message)
- because they are ordinary files in a folder, you can open the same folder in Obsidian on your
  own computer and read or edit everything

Two scripts keep the web side of it current:

| Script | Output |
|---|---|
| `vault/build-vault-site.py` | the vault pages (`index.html`), the graph data (`graph.json`) and the graph page (`graph.html`) |
| `vault/vault-graph.tpl` | the graph page itself: an Obsidian-style force graph — drag, zoom, hover, filter, click a dot to open its note |

Run it from a timer (we use every two minutes) so notes appear shortly after the bot writes them.

## The Help pages and the OpenRouter key form

`help/build-help-pages.py` generates one Help page per deployment, explaining what the platform
is, every feature, the vault and memory, Skills, and how to set up OpenRouter — including a form
that saves a new API key.

The form posts to `/save-key`, which is handled by `services/save-key-service.py`:

1. Caddy adds the deployment's name and a shared secret to the request
2. the service checks the secret and the key's shape
3. it writes `OPENAI_API_KEY=` into **that deployment's `.env`**
4. it restarts **that container only**

The Help page also shows the model the agents are running on and whether a key is set, fetched
live from `/info` on the same service.

Each deployment has its own `.env`, so one deployment's key never affects another.

## The login gate

Caddy (`deploy/Caddyfile.example`) sits in front of everything. With `basic_auth` on a site
block, the app is one username and password. Leave it off for a deployment you want open — but
remember that an open deployment means anyone can use its bots and change its OpenRouter key.

## Skills and routines

- **Skills** are named instructions a bot can be told to follow, invoked with `/`. They grant
  nothing: the bot may still only do what it has been granted, and every action is still recorded.
- **Routines** are scheduled instructions ("every weekday at 9, …"). They need a worker process;
  see the upstream OpenBot docs.

## Where each piece lives

| Piece | File |
|---|---|
| Branding of the app shell and sidebar | `branding/` |
| One deployment's settings and keys | `deploy/.env.example` |
| The bots themselves | `tenant-package/agents.yaml` |
| The vault pages and graph | `vault/` |
| The Help pages | `help/` |
| The OpenRouter key endpoint | `services/save-key-service.py` |
| The login gate and routing | `deploy/Caddyfile.example` |
| Publishing on a domain | `deploy/cloudflared-config.example.yml` |
