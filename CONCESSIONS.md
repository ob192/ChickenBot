# Concessions

Deliberate trade-offs and shortcuts in the current implementation, with the "proper"
alternative each one displaces. None of these are bugs — they are choices that fit the
project's current size and may need revisiting as it grows.

## Schema managed by `CREATE TABLE IF NOT EXISTS`

Tables and indexes are created at startup in `bot/db.py` instead of using a migration tool
(Alembic, dbmate, …). Simple and zero-ops, but **existing tables are never altered** — any
future column change requires either manual SQL against Neon or adopting a migration tool
at that point.

## No ORM — raw SQL over asyncpg

Queries are hand-written SQL strings. Fine at 3 queries; if the query count grows
significantly, SQLAlchemy Core/ORM would buy type safety and composability at the cost of
a heavier stack.

## `channel_binding` stripped in code

asyncpg cannot parse Neon's `channel_binding=require` DSN parameter, so `_clean_dsn()`
removes it at connect time rather than editing the stored secret. This keeps `.env`
byte-identical to what Neon issues, but means the channel-binding hardening is simply not
applied (TLS via `sslmode=require` still is).

## Outgoing `user_id` inferred from `chat_id`

For outgoing messages, `user_id` is set to `chat_id` when it is positive (private chat)
and left `NULL` for groups/channels. Telegram does not echo a "recipient user" for API
calls, so this heuristic is as good as it gets without joining against chat membership.

## Outgoing payload drops aiogram `Default` sentinels

aiogram method objects carry `Default(...)` placeholders for unset options (parse mode,
etc.). The JSONB payload serializes them as `null` via a pydantic fallback rather than
resolving what the session actually sent. The delivered text/content is always captured;
only the *effective defaults* are not.

## Logging failures are swallowed

All three middlewares catch every exception, log it, and let the update proceed.
Availability of the bot is prioritized over completeness of the audit trail — if the DB is
down, conversations continue but are not recorded.

## `requirements.txt` kept alongside `pyproject.toml`

uv + `pyproject.toml` + `uv.lock` is the source of truth; `requirements.txt` is a
convenience mirror for pip-only environments and can drift if only one is updated.

## Single-instance long polling

Polling is simpler than webhooks (no public endpoint, no TLS certs) but caps the
deployment at exactly one instance. Moving to webhooks is the path to horizontal scaling
or zero-downtime deploys.

## Full raw payloads stored forever

Every update and API call is stored as JSONB with no retention policy. Cheap now; at
scale this table grows unboundedly and may accumulate personal data that warrants a
retention/cleanup policy.
