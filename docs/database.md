# Persistence

## Connection

- Provider: [Neon](https://neon.tech/) serverless Postgres (pooled endpoint, us-east-2).
- Driver: [asyncpg](https://magicstack.github.io/asyncpg/) with a pool of 1–5 connections.
- DSN comes from the `DATABASE_URL` env var (see [configuration.md](configuration.md)).

[`core/db.py`](../core/db.py) owns all SQL and is shared by the bot and the
[API](api.md) — both open their own pool against the same database. `create_pool()`
connects, creates any missing tables/indexes (`CREATE TABLE IF NOT EXISTS`), adds the
access columns to a pre-existing `users` table (`ALTER TABLE … ADD COLUMN IF NOT EXISTS`)
and seeds the default settings rows. There is no separate migration step.

**asyncpg quirk:** asyncpg does not understand the `channel_binding` query parameter that
Neon includes in its connection strings for libpq clients. `_clean_dsn()` strips it before
connecting; the value in `.env` stays exactly as Neon issued it.

## Schema

### `users` — everyone the bot has interacted with

| Column              | Type        | Notes                                        |
| ------------------- | ----------- | -------------------------------------------- |
| `telegram_id`       | BIGINT PK   | Telegram user id                             |
| `username`          | TEXT        | may be null                                  |
| `first_name`        | TEXT        | not null                                     |
| `last_name`         | TEXT        |                                              |
| `language_code`     | TEXT        |                                              |
| `is_premium`        | BOOLEAN     |                                              |
| `first_seen_at`     | TIMESTAMPTZ | set on first insert                          |
| `last_seen_at`      | TIMESTAMPTZ | refreshed on every interaction               |
| `access_status`     | TEXT        | `pending` / `allowed` / `blocked` (checked)  |
| `access_note`       | TEXT        | why the decision was made                    |
| `access_updated_at` | TIMESTAMPTZ | when access last changed                     |

Upserted on every incoming update (`ON CONFLICT (telegram_id) DO UPDATE`), so profile
changes (new username, etc.) are picked up automatically. The upsert deliberately leaves
the three `access_*` columns alone — only the API writes them. Rows can also be created by
the API to pre-authorize someone who has never written in; see
[access-control.md](access-control.md).

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
Messages sent through the API land here too — same middleware, same shape.

### `settings` — runtime switches shared by the bot and the API

| Column       | Type        | Notes                     |
| ------------ | ----------- | ------------------------- |
| `key`        | TEXT PK     |                           |
| `value`      | TEXT        | always stored as text     |
| `updated_at` | TIMESTAMPTZ | refreshed on every write  |

| Key                     | Default                                        | Meaning                                   |
| ----------------------- | ---------------------------------------------- | ----------------------------------------- |
| `bot_enabled`           | `true`                                         | `false` silences the bot entirely         |
| `access_mode`           | `open`                                         | `open` or `allowlist`                     |
| `access_denied_message` | `Sorry, you don't have access to this bot.`    | reply sent to refused users (empty = mute)|

Seeded on startup with `ON CONFLICT DO NOTHING`, so an operator's changes survive restarts.
The bot re-reads them at most every 5 seconds — this table is how the API steers a bot
process it does not share memory with.

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

Who is currently allowed in:

```sql
SELECT telegram_id, username, access_status, access_note, access_updated_at
FROM users WHERE access_status <> 'pending' ORDER BY access_updated_at DESC;
```
