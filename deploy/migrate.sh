#!/bin/sh
# Migrations, for the embedded database only.
#
# An external database is somebody else's release process: two replicas starting together would
# race, and a failed migration should stop a deploy rather than leave a half-migrated database
# serving. An embedded one has exactly one process and no deploy pipeline, so doing it here is the
# difference between the container working and the operator reading a runbook.
#
# This copy adds one thing the image's own script lacks: it waits for the embedded postgres to
# accept connections before running. Without it, migrate races the server's startup and fails with
# "the database system is starting up", which stops `api` from ever starting.
set -eu
[ "${EMBEDDED_POSTGRES:-off}" = "on" ] || exit 0

if [ "${EMBEDDED_POSTGRES:-off}" = "on" ]; then
  i=0
  while ! pg_isready -h 127.0.0.1 -p 5432 -U openbot >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge 90 ]; then
      echo "migrate: postgres not ready after 90s, giving up" >&2
      exit 1
    fi
    sleep 1
  done
fi

cd /app/server
export HOME=/home/apiuser
# `scripts/migrate.ts`, not `drizzle-kit`. The CLI is a development dependency and needs esbuild to
# read its TypeScript config, which `bun install --production` leaves out of this image: asked to
# migrate here it exits 1 without printing why, and the container comes up against an empty database.
exec s6-setuidgid apiuser /usr/local/bin/bun scripts/migrate.ts