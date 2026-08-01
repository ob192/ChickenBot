# ChickenBot

A Telegram bot built with [aiogram 3](https://docs.aiogram.dev/) that records every user it
talks to — and the full conversation history — in Postgres ([Neon](https://neon.tech/)).

Full documentation lives in [INDEX.md](INDEX.md).

## Quick start

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Copy `.env.example` to `.env` and fill in the values (bot token from
   [@BotFather](https://t.me/BotFather), Postgres connection string):

   ```bash
   cp .env.example .env
   ```

3. Run the bot:

   ```bash
   make run
   ```

## Make targets

| Target        | What it does                                                        |
| ------------- | ------------------------------------------------------------------- |
| `make run`    | Run the bot locally with uv                                         |
| `make build`  | Build the docker image `sasha192bunin/chickenbot`                   |
| `make deploy` | Build and push the image to Docker Hub                              |
| `make up`     | Run the image as a local container (uses `.env`, auto-restarts)     |
| `make stop`   | Stop and remove the container                                       |
| `make logs`   | Follow container logs                                               |

## Project layout

```
main.py              entry point: wiring, polling loop
bot/config.py        env loading (.env.local overrides .env)
bot/handlers.py      command/message handlers
bot/middlewares.py   user storage + full message logging (both directions)
bot/db.py            asyncpg pool, schema, queries
chiken/              game mode images (Easy/Medium/Hard) — not wired up yet
docs/                domain documentation, see INDEX.md
```
