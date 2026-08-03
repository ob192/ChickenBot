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

### Checking it works

```bash
curl http://localhost:8000/health                                  # {"status":"ok","database":"ok"}
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/bot/status  # identity + counters
```

`/api/bot/status` reporting `"reachable": true` means the token is good and Telegram
answered. The bot logs `Run polling for bot @yourbot` once it is up.

### If a port is taken

The API port is a Makefile variable, the admin port a `next dev` flag:

```bash
make api API_PORT=8001
cd admin && npm run dev -- -p 3001
```

Point the admin UI at a moved API with `API_BASE_URL` in `admin/.env.local`.

### Running only some services

They are independent processes that meet in Postgres:

- the **bot** runs without the API — it just loses remote control;
- the **API** runs without the bot, and without a valid `TELEGRAM_BOT_TOKEN` — access
  control and the message log work, only sending is disabled (`503`);
- the **admin UI** needs the API, and shows a diagnostic banner when it cannot reach it.

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
api/schemas.py            pydantic request/response models
api/routers/              bot control, users, access, messages

admin/app/                Next.js App Router pages (dashboard, users, messages)
admin/app/api/proxy/      forwards browser calls, injecting the API key server-side
admin/components/         interactive client components
admin/lib/                server-side + browser-side API clients

Dockerfile                python image — bot (default CMD) and api (CMD override)
admin/Dockerfile          admin UI image
docker-compose.yml        all three services wired together

chiken/                   game mode images (Easy/Medium/Hard) — not wired up yet
docs/                     domain documentation, see INDEX.md
```
