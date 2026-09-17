# Help pages

`build-help-pages.py` writes one Help page per deployment into `help-site/<slug>/index.html`,
explaining what the platform is, its features, the vault and memory, Skills, and how to set up
OpenRouter — with a form that saves a new API key.

Edit the `SITES` list at the top for your deployments (name, URL, env file, container), then run
it from a timer. Caddy serves the output at `/help/` for each site (see
`deploy/Caddyfile.example`).
