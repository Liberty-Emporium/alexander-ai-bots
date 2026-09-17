#!/usr/bin/env bash
# Start one Alexander AI Solutions bots deployment.
#
#   ./docker-run.example.sh <name> <host-port> [folder]
#
# Everything that makes the deployment yours lives in its own folder:
#   <folder>/.env              secrets and settings (deploy/.env.example)
#   <folder>/tenant/           the bots, channels, brand, model
#   <folder>/migrate.sh        postgres-readiness wrapper for the migration
#   <folder>/vault/            the bot's Obsidian vault (mounted as /workspace)
#   <folder>/branding/         the branded page shell and its assets
set -euo pipefail

NAME="${1:?usage: docker-run.example.sh <name> <host-port> [folder]}"
PORT="${2:?usage: docker-run.example.sh <name> <host-port> [folder]}"
FOLDER="${3:-$HOME/$NAME}"
IMAGE="ghcr.io/copilotkit/openbot:latest"

mkdir -p "$FOLDER"/{tenant,vault,branding}

docker run -d --name "$NAME" \
  --restart unless-stopped \
  --security-opt seccomp=unconfined \
  --shm-size=1g \
  -p "${PORT}:3001" \
  --env-file "$FOLDER/.env" \
  -v "${NAME}-data:/var/lib/postgresql" \
  -v "${NAME}-profiles:/profiles" \
  -v "$FOLDER/tenant:/tenant" \
  -v "$FOLDER/migrate.sh:/etc/s6-overlay/scripts/migrate.sh" \
  -v "$FOLDER/vault:/workspace" \
  -v "$FOLDER/branding/index.html:/app/app/dist/index.html" \
  -v "$FOLDER/branding/app-bundle.js:/app/app/dist/assets/index-CbN6XavV.js" \
  -v "$FOLDER/branding/hero.png:/app/app/dist/alexander-hero-2.png" \
  -v "$FOLDER/branding/favicon.png:/app/app/dist/favicon.png" \
  "$IMAGE"

echo "Started $NAME on http://localhost:$PORT"
echo "Next: put it on a domain with deploy/Caddyfile.example and a Cloudflare tunnel."
