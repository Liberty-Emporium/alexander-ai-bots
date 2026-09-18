# Mobile API map

Every endpoint below was read from the running OpenBot v0.0.12 server source
(`/app/server/src`). Nothing here is guessed. All paths are relative to the deployment's
base URL (for example `https://alexander-bot.jays-web.org`).

## Authentication and identity

| Method | Path | Purpose | Notes |
|---|---|---|---|
| GET | `/api/me` | the signed-in person | in single-user mode returns the one admin |
| GET | `/api/me/onboarding` | onboarding state | |
| GET | `/api/capabilities` | what this deployment can do | feature discovery for the client |
| GET | `/api/agents/capabilities` | per-bot capabilities | |
| POST | `/api/auth/sign-out` | sign out | better-auth |
| POST | `/api/auth/sso/register` | register an SSO provider | admin |
| GET | `/api/auth/...` | better-auth handlers | session cookies |

Single-user deployments: no in-app login; the entry point is the gate in front of the app.
Multi-user: better-auth session cookie, or SSO.

## Bots (coworkers)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/agents` | list bots |
| POST | `/api/agents` | create a bot |
| GET | `/api/agents/:id` | one bot |
| DELETE | `/api/agents/:id` | remove a bot |
| GET | `/api/agents/capabilities` | what a bot may do |

## Chat and conversations

| Method | Path | Purpose | Notes |
|---|---|---|---|
| POST | `/api/threads/mint` | mint a thread id for a new conversation | durable thread in Intelligence |
| GET | `/api/threads/:id` | thread state | `known` / unavailable |
| POST | `/api/copilotkit` | **the chat runtime** | streams **SSE** (`text/event-stream`) |

The chat client speaks the CopilotKit runtime protocol at `/api/copilotkit`, exactly as the web
app does. This is the one surface where a native client must match a protocol rather than call a
plain REST endpoint.

## Channels (conversations as rooms)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/channels` | list channels |
| POST | `/api/channels` | create a channel (`agentIds`) |
| GET | `/api/channels/:id` | one channel |
| DELETE | `/api/channels/:id` | remove |
| PUT | `/api/channels/:id/read` | mark read |
| PUT | `/api/channels/:id/pin` | pin |
| POST | `/api/channels/:id/activity` | record activity |
| GET | `/api/channels/events` | **live updates, SSE** |

`/api/channels/events` is the realtime feed for channel activity — use it rather than polling.

## The bot computer (through the gateway only)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/computers/:botId/status` | is a browser running |
| GET | `/api/computers/:botId/screenshot` | current screen (PNG, base64 JSON) |
| GET | `/api/computers/:botId/read` | page as readable text |
| GET | `/api/computers/:botId/page-frame/:toolCallId` | the frame a tool call produced |
| POST | `/api/computers/:botId/navigate` | open a URL |
| POST | `/api/computers/:botId/snapshot` | actionable elements (refs) |
| POST | `/api/computers/:botId/click` | click a ref |
| POST | `/api/computers/:botId/type` | type into a ref |
| POST | `/api/computers/:botId/key` | press a key |
| POST | `/api/computers/:botId/scroll` | scroll |
| GET | `/api/computers/:botId/control` | who holds the wheel |
| POST | `/api/computers/:botId/control/request` | bot asks for help |
| POST | `/api/computers/:botId/control/take` | a person takes the wheel |
| POST | `/api/computers/:botId/control/release` | hand it back |
| POST | `/api/computers/:botId/control/secret` | bot asks for one secret |
| POST | `/api/computers/:botId/human/secret` | person supplies it |
| POST | `/api/computers/:botId/human/:kind` | person input (click/type/scroll) |
| POST | `/api/computers/:botId/files/list` | list workspace files |
| POST | `/api/computers/:botId/files/read` | read a file |
| POST | `/api/computers/:botId/files/write` | write a file |
| POST | `/api/computers/:botId/exec` | run a command in the workspace |
| GET | `/api/computers/fleet` | all bots' computers |
| POST | `/api/computers/:botId/computers/stop` | stop the browser |
| POST | `/api/computers/:botId/computers/reset` | wipe and start over |
| GET | `/api/computers/policy` | the action policy |
| POST | `/api/computers/policy-dry-run` | test a policy change |

For a live screen, poll `screenshot` on a short interval (the web app does the same). The
computer's own websocket stream is internal and must not be exposed.

## Activity and governance

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/admin/audit-events` | the audit trail: permitted, refused, failed |
| GET | `/api/admin/status` | deployment status |
| GET | `/api/admin/package` | tenant package status |
| GET | `/api/admin/people` | people and roles |
| GET | `/api/admin/credentials` | stored credentials (write-only values) |
| POST | `/api/admin/credentials` | add a credential (`kind`, `provider`, `keyId`, `metadata`, `plaintext`) |
| GET | `/api/admin/identity-providers` | SSO providers |

The audit trail is the activity feed: it already records every action with the bot, the action,
the target and the decision. A mobile Activity screen should read this rather than duplicate it.

## Skills, routines, plugins, components

| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/api/routines` | scheduled work |
| GET/POST | `/api/plugins/skills` | deployment skills |
| GET | `/api/plugins` | connectors, grants, catalogue |
| POST | `/api/plugins/servers/custom` | add an MCP server (`id`, `title`, `url`, `credentialId`) |
| POST | `/api/plugins/grants` | grant tools to a bot |
| GET/POST | `/api/components` | generated UI components |
| GET/POST | `/api/attachments` | files attached to messages |

## What is deliberately absent

- **No push notification endpoint.** Nothing in OpenBot forwards events to APNs/FCM. A mobile
  notifications feature requires new backend work: an event source (already present in the
  channel event hub and the audit trail), a device registry, and a sender.
- **No mobile-specific API.** There is no `/api/mobile`. The client uses the same surface as the
  web app, which is the intended design.
- **No direct computer access.** The computer service is loopback-only with its own token.

## Reachability from a phone

The API is served from the same origin as the app and passes through the same gate:

```
https://<deployment-host>/api/...      (Caddy gate → server)
https://<deployment-host>/api/copilotkit      (SSE)
https://<deployment-host>/api/channels/events (SSE)
```

SSE works through the gate and the Cloudflare tunnel; no separate host or port is required.
