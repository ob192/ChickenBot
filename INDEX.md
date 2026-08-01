# ChickenBot — documentation index

Start here. Each document covers one domain of the project.

## Overview

- [README.md](README.md) — what the bot is, quick start, make targets, project layout.

## Domains

- [docs/bot.md](docs/bot.md) — **Bot runtime**: entry point, dispatcher, handlers, middleware
  pipeline, how updates flow through the system.
- [docs/database.md](docs/database.md) — **Persistence**: Neon Postgres connection, schema
  (`users`, `messages` tables), queries, asyncpg specifics.
- [docs/configuration.md](docs/configuration.md) — **Configuration**: environment variables,
  `.env` / `.env.local` precedence, secrets handling.
- [docs/deployment.md](docs/deployment.md) — **Deployment**: Docker image, Docker Hub
  publishing, Makefile targets, running on a server.

## Project state

- [CONCESSIONS.md](CONCESSIONS.md) — deliberate trade-offs and shortcuts taken, and what the
  "proper" alternative would be.
- [ISSUES.md](ISSUES.md) — known issues and open work items.
