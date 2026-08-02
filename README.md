# ChickenBot

A Telegram bot built with [aiogram 3](https://docs.aiogram.dev/) that records every user it
talks to — and the full conversation history — in Postgres ([Neon](https://neon.tech/)),
plus a FastAPI control plane and a Next.js admin panel for running it.

```
Telegram ──▶ telegram_bot  ──┐
                             ├──▶  Postgres  ◀──  api (FastAPI)  ◀──  admin (Next.js)
             (long polling) ─┘      users / messages / settings
```

The bot and the API share `core/` (config + database), so the API can change how the bot
behaves — who may use it, whether it answers at all — without restarting or redeploying it.

Full documentation lives in [INDEX.md](INDEX.md).

## Quick start

Requires [uv](https://docs.astral.sh/uv/), Python 3.12+ and Node 20+.

1. Install dependencies:

   ```bash
   uv sync && (cd admin && npm install)
   ```

2. Copy `.env.example` to `.env` and fill in the values — bot token from
   [@BotFather](https://t.me/BotFather), Postgres connection string, and an API key
   (`openssl rand -hex 32`):

   ```bash
   cp .env.example .env
   ```

3. Point the admin UI at the API with the same key:

   ```bash
   cp admin/.env.example admin/.env.local
   ```

4. Run the three processes (separate terminals), or `make dev` for all of them in Docker:

   ```bash
   make bot     # Telegram bot
   make api     # http://localhost:8000/docs
   make admin   # http://localhost:3000
   ```

## Make targets

| Target             | What it does                                                        |
| ------------------ | ------------------------------------------------------------------- |
| `make bot`         | Run the Telegram bot locally with uv                                |
| `make api`         | Run the FastAPI service locally with auto-reload                    |
| `make admin`       | Run the Next.js admin UI locally                                    |
| `make dev`         | Run the whole stack with docker compose                             |
| `make build`       | Build the python image `sasha192bunin/chickenbot`                   |
| `make build-admin` | Build the admin image `sasha192bunin/chickenbot-admin`              |
| `make deploy`      | Build and push both images to Docker Hub                            |
| `make up`          | Start the stack detached (uses `.env`, auto-restarts), then tail logs |
| `make stop`        | Tear the stack down                                                 |
| `make logs`        | Follow logs of all services                                         |

## Project layout

```
core/config.py            env loading (.env.local overrides .env), shared by bot + api
core/db.py                asyncpg pool, schema, all SQL

telegram_bot/main.py      entry point: wiring, polling loop
telegram_bot/handlers.py  command/message handlers
telegram_bot/middlewares.py  user storage, message logging, access enforcement

api/main.py               FastAPI app, lifespan, CORS, /health
api/deps.py               X-API-Key auth + shared dependencies
api/routers/              bot control, users, access, messages

admin/app/                Next.js App Router pages (dashboard, users, messages)
admin/components/         interactive client components
admin/lib/                server-side + browser-side API clients

chiken/                   game mode images (Easy/Medium/Hard) — not wired up yet
docs/                     domain documentation, see INDEX.md
```
