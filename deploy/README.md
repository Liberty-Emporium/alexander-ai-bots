# Deployment kit

Everything needed to put one Alexander AI Solutions bots deployment online.

| File | What it is |
|---|---|
| `.env.example` | The settings and keys for one deployment. Copy to `.env` and fill in. |
| `docker-run.example.sh` | Starts one deployment as a container, with its own database, browser profiles, tenant package and vault. |
| `migrate.sh` | A small wrapper that makes the container's database migration wait for Postgres. Mounted over the image's copy. |
| `Caddyfile.example` | The login gate, the Help pages, and the OpenRouter key endpoints. |
| `cloudflared-config.example.yml` | Publishes the deployment on your domain through a Cloudflare tunnel — no open ports. |

Each deployment keeps its **own `.env`**, so one deployment's keys and settings never affect
another. Run several by repeating `docker-run.example.sh` with a different name and port.
