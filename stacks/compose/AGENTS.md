---
name: compose
description: Docker compose-first development — one Dockerfile with dev/runtime targets, commands run inside the stack, secrets never in an image
route: Docker / compose dev stack
---
# Compose — dev stack

**Read when:** running any service, editing a `Dockerfile` or `compose.yml`, or anything about
how a service starts.
**Prereq:** `../workflow.md`

The stack is **compose-first**. `docker compose up` is the development environment; a
bare-metal run is a fallback for one service, not the normal path. Startup instructions and
the service table live in the project README — this file is the rules.

---

## Layout

```
compose.yml · .env.example       the dev stack; .env is gitignored
<service>/Dockerfile             targets: dev · runtime (default)
```

One Dockerfile per service covers both environments. `--target dev` installs the dev
dependencies and expects the working tree mounted over it; the `runtime` target is
production — no dev tooling, no source mount.

**Compose builds `dev` and only `dev`.** `runtime` is deployed elsewhere, so nothing in it
may assume a compose network — a service name like `api:8000` resolves on that bridge and
nowhere else. Production wiring is environment variables set by the platform, and CI names
`target: runtime` explicitly rather than relying on stage order.

## Non-negotiables

1. **Run commands against the stack, not the host.** `docker compose exec api pytest`,
   `docker compose exec web npm run test`. The `uv run` / `npm run` forms in the stack files
   are the bare-metal equivalents of the same commands, not a second way of working.
2. **One-shot services order the setup.** A `migrate` service runs to completion before
   `api` and `worker` start; a provisioning service creates buckets/containers before the
   first upload. Startup-time migration in the app is a convenience, not a serialisation
   guarantee across replicas.
3. **The worker is part of the stack.** Drop it and a request that enqueues still returns
   201 while the queue silently grows — a queue that accumulates looks exactly like one that
   works.
4. **The SPA stays same-origin with the API.** The dev server proxies `/api`, which is what
   makes the session cookie first-party and lets CORS stay empty. Do not "fix" a failing
   request by opening CORS.
5. **No new service, image or base-image bump without asking.** Same rule as a dependency.
6. **Secrets are never baked into an image or a `Dockerfile`.** Compose defaults are
   local-only and labelled as such; anything real arrives as an environment variable at run
   time.
7. **A dev-only convenience never reaches the default target.** Reload flags, mounted source
   and dev dependencies belong to `--target dev` and to `compose.yml`.

## Changing how a service starts

Put the fact in exactly one place, then let the others inherit it:

| Fact | Its home |
| --- | --- |
| Host/port the dev server binds, allowed hostnames | the dev server's config file |
| Dependencies present in an image | the `Dockerfile` target |
| Reload flags, mounts, ordering, env | `compose.yml` |
| Production command, user, healthcheck | the `Dockerfile` `runtime` target |
| Where the deployed frontend sends `/api` | an environment variable set by the deployment, with no default |

A flag repeated in two of those will be changed in one of them and silently ignored in the
other.

## Gotchas

- **`.venv` and `node_modules` are named volumes** shadowing the mounted tree. They are not
  refreshed by a rebuild. After editing `uv.lock` or `package-lock.json`:
  `docker compose down -v && docker compose up --build`.
- **The container healthcheck is liveness, not readiness.** Keep it a TCP connect; point an
  orchestrator's readiness probe at the `/health` endpoint that pings dependencies. A
  dependency blip must not mark healthy replicas unhealthy.
- **A static server must 404 a missing hashed asset**, not fall back to `index.html` — the
  fallback surfaces as a MIME-type error.
- **A required deployment variable has no default, and the image refuses to start without
  it.** An empty upstream is *valid* config: the container boots, probes go green, and only
  `/api/*` fails.
- **Reaching the stack through a tunnel needs the hostname allow-listed** on the dev server.
  Name the host rather than disabling the check — it is DNS-rebinding protection, and the
  dev stack is not hardened for public exposure (the committed `SECRET_KEY` default signs
  sessions). Override it in `.env` before exposing the stack.
- **A service's own `.env` file is outranked by compose-injected variables.** The stack's
  `.env` is the override file.

**See also:** `../fastapi/AGENTS.md` · `../react/AGENTS.md` · `../workflow.md`
