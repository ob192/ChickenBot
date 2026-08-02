# Configuration

All Python configuration is via environment variables, loaded once by
[`core/config.py`](../core/config.py) using `python-dotenv` and shared by the bot and the
API. The admin UI has its own, separate env file.

## Python services (`.env` in the project root)

| Variable             | Required        | Description                                             |
| -------------------- | --------------- | ------------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | yes for the bot | Bot token from [@BotFather](https://t.me/BotFather)     |
| `DATABASE_URL`       | yes             | Postgres DSN, e.g. `postgresql://user:pass@host/db?sslmode=require` |
| `API_KEY`            | yes for the API | Shared secret clients send as `X-API-Key`; generate with `openssl rand -hex 32` |
| `CORS_ORIGINS`       | no              | Comma-separated browser origins allowed to call the API (default `http://localhost:3000`) |

`TELEGRAM_BOT_TOKEN` and `DATABASE_URL` are read with `os.environ[...]`, so both services
fail fast at startup if either is missing entirely. The two keys degrade rather than crash
when set to something unusable:

- an **invalid or empty bot token** stops the bot (aiogram refuses to start), but the API
  keeps running with sending disabled — see [api.md](api.md);
- a **missing `API_KEY`** makes every authenticated API route return `503`, so the API is
  never accidentally open.

## Admin UI (`admin/.env.local`)

| Variable       | Required | Description                                                |
| -------------- | -------- | ---------------------------------------------------------- |
| `API_BASE_URL` | yes      | Where FastAPI lives, no trailing slash (`http://localhost:8000`) |
| `API_KEY`      | yes      | Must match the API's `API_KEY`                             |

Neither is prefixed with `NEXT_PUBLIC_`, so both stay in the Next.js server process — see
[admin-ui.md](admin-ui.md).

## File precedence

`load_dotenv` never overrides variables that are already set, and `.env.local` is loaded
first, so the effective order is:

1. Real environment variables (highest priority — this is how Docker injects config)
2. `.env.local` — personal/local overrides, gitignored
3. `.env` — defaults, gitignored

`.env.example` (root) and `admin/.env.example` are the committed templates listing every
variable with an empty value.

## Secrets handling

- `.env`, `.env.local` and `admin/.env*` are in `.gitignore` and the `.dockerignore` files
  — secrets are never committed or baked into an image.
- Containers get their config at runtime via `--env-file` / compose `environment` (see
  [deployment.md](deployment.md)).
- The Neon `DATABASE_URL` includes `channel_binding=require`, which the asyncpg driver
  strips at connect time (see [database.md](database.md)) — keep the value as Neon issues it.
- The API key is the only credential the admin UI holds, and only server-side. Rotating it
  means updating the root `.env` and `admin/.env.local` together.
