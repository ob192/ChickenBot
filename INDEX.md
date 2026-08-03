# ChickenBot — documentation index

Start here. Each document covers one domain of the project.

## Overview

- [README.md](README.md) — what the project is, architecture sketch, quick start, make
  targets, project layout.

## Domains

- [docs/bot.md](docs/bot.md) — **Bot runtime** (`telegram_bot/`): entry point, dispatcher,
  handlers, middleware pipeline, how updates flow through the system.
- [docs/api.md](docs/api.md) — **API** (`api/`): FastAPI control plane, authentication,
  endpoint reference, sending messages as the bot.
- [docs/admin-ui.md](docs/admin-ui.md) — **Admin UI** (`admin/`): Next.js panel, pages,
  how it talks to the API without exposing the key.
- [docs/access-control.md](docs/access-control.md) — **Access control**: who may use the
  bot, the global mode, per-user statuses, the kill switch, enforcement.
- [docs/database.md](docs/database.md) — **Persistence** (`core/`): Neon Postgres
  connection, schema (`users`, `messages`, `settings`), queries, asyncpg specifics.
- [docs/configuration.md](docs/configuration.md) — **Configuration**: environment variables
  for every service, `.env` / `.env.local` precedence, secrets handling.
- [docs/deployment.md](docs/deployment.md) — **Deployment**: Docker images, compose stack,
  Docker Hub publishing, Makefile targets, running on a server.

## Project state

- [CONCESSIONS.md](CONCESSIONS.md) — deliberate trade-offs and shortcuts taken, and what the
  "proper" alternative would be.
- [ISSUES.md](ISSUES.md) — known issues and open work items.
