# Persistence

## Connection

- Provider: [Neon](https://neon.tech/) serverless Postgres (pooled endpoint, us-east-2).
- Driver: [asyncpg](https://magicstack.github.io/asyncpg/) with a pool of 1–5 connections.
- DSN comes from the `DATABASE_URL` env var (see [configuration.md](configuration.md)).

[`bot/db.py`](../bot/db.py) owns all SQL. `create_pool()` connects and creates any missing
tables/indexes (`CREATE TABLE IF NOT EXISTS`) — there is no separate migration step.

**asyncpg quirk:** asyncpg does not understand the `channel_binding` query parameter that
Neon includes in its connection strings for libpq clients. `_clean_dsn()` strips it before
connecting; the value in `.env` stays exactly as Neon issued it.

## Schema

### `users` — everyone the bot has interacted with

| Column          | Type        | Notes                          |
| --------------- | ----------- | ------------------------------ |
| `telegram_id`   | BIGINT PK   | Telegram user id               |
| `username`      | TEXT        | may be null                    |
| `first_name`    | TEXT        | not null                       |
| `last_name`     | TEXT        |                                |
| `language_code` | TEXT        |                                |
| `is_premium`    | BOOLEAN     |                                |
| `first_seen_at` | TIMESTAMPTZ | set on first insert            |
| `last_seen_at`  | TIMESTAMPTZ | refreshed on every interaction |

Upserted on every incoming update (`ON CONFLICT (telegram_id) DO UPDATE`), so profile
changes (new username, etc.) are picked up automatically.

### `messages` — full conversation log, both directions

| Column                | Type          | Notes                                            |
| --------------------- | ------------- | ------------------------------------------------ |
| `id`                  | BIGSERIAL PK  |                                                  |
| `direction`           | TEXT          | `'in'` (from user) or `'out'` (from bot)         |
| `chat_id`             | BIGINT        | indexed together with `created_at`               |
| `user_id`             | BIGINT        | sender for `in`; chat partner for private `out`  |
| `event_type`          | TEXT          | `message`, `callback_query`, … / `sendMessage`, …|
| `text`                | TEXT          | text, caption, or callback data                  |
| `telegram_message_id` | BIGINT        |                                                  |
| `payload`             | JSONB         | full raw update / API call                       |
| `created_at`          | TIMESTAMPTZ   | insert time                                      |

`payload` keeps everything Telegram sent (or the bot sent), so media metadata, keyboards,
entities, etc. are queryable with JSONB operators even though only `text` is extracted.

## Useful queries

Conversation with one user, in order:

```sql
SELECT created_at, direction, event_type, text
FROM messages WHERE chat_id = <telegram_id>
ORDER BY created_at;
```

Most recently active users:

```sql
SELECT telegram_id, username, first_name, last_seen_at
FROM users ORDER BY last_seen_at DESC LIMIT 20;
```
