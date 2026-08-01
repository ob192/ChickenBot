# Configuration

All configuration is via environment variables, loaded by
[`bot/config.py`](../bot/config.py) using `python-dotenv`.

## Variables

| Variable             | Required | Description                                             |
| -------------------- | -------- | ------------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | yes      | Bot token from [@BotFather](https://t.me/BotFather)     |
| `DATABASE_URL`       | yes      | Postgres DSN, e.g. `postgresql://user:pass@host/db?sslmode=require` |

Both are read with `os.environ[...]` — the bot fails fast at startup if either is missing.

## File precedence

`load_dotenv` never overrides variables that are already set, and `.env.local` is loaded
first, so the effective order is:

1. Real environment variables (highest priority — this is how Docker injects config)
2. `.env.local` — personal/local overrides, gitignored
3. `.env` — defaults, gitignored

`.env.example` is the committed template listing every variable with an empty value.

## Secrets handling

- `.env` and `.env.local` are in both `.gitignore` and `.dockerignore` — secrets are never
  committed or baked into the image.
- Containers get their config at runtime via `--env-file` (see
  [deployment.md](deployment.md)).
- The Neon `DATABASE_URL` includes `channel_binding=require`, which the asyncpg driver
  strips at connect time (see [database.md](database.md)) — keep the value as Neon issues it.
