# Concessions

Deliberate trade-offs and shortcuts in the current implementation, with the "proper"
alternative each one displaces. None of these are bugs — they are choices that fit the
project's current size and may need revisiting as it grows.

## Schema managed by `CREATE TABLE IF NOT EXISTS` + ad-hoc `ALTER`

Tables and indexes are created at startup in `core/db.py` instead of using a migration tool
(Alembic, dbmate, …). The access columns added to the pre-existing `users` table are
handled by a hand-written `ALTER TABLE … ADD COLUMN IF NOT EXISTS` list that runs on every
startup. It is idempotent and zero-ops, but it only grows — column *changes* and drops
still need manual SQL, and the list is a migration history with no ordering or versioning.
A second schema change of this size is the moment to adopt a real migration tool.

## No ORM — raw SQL over asyncpg

Queries are hand-written SQL strings. Still readable at ~15 queries, and `list_users()`
already builds its `WHERE` clause by string concatenation with positional placeholders —
correct and injection-safe, but the pattern does not scale. More filters, joins or sorts
would justify SQLAlchemy Core.

## Both services connect to the same database directly

The API does not go through the bot, and the bot does not go through the API — each opens
its own asyncpg pool against the same tables, and they coordinate through the `settings`
table. That keeps the bot alive when the API is down (and vice versa) at the cost of two
writers to one schema and a propagation delay of up to 5 seconds on settings changes. An
internal RPC or a message queue would be the "proper" answer at the point where more than
two processes need to coordinate.

## Single shared API key, no user accounts

Every API client authenticates with one static `X-API-Key`. There is no per-operator
identity, so the audit trail cannot say *who* blocked a user, and rotating the key means
updating every client. Real admin accounts (OAuth/JWT + roles) are the alternative, and
would also let the admin UI have a login of its own.

## The admin UI has no authentication

`admin/` holds the API key server-side and proxies browser calls, so the key never reaches
the client — but anyone who can open the page can use it. It is meant to run on localhost
or behind a VPN / authenticating reverse proxy. Adding a login (NextAuth or a proxy that
enforces SSO) is the fix before exposing it publicly.

## Access denial replies on every message

A refused user gets `access_denied_message` on every plain message they send — there is no
rate limit or "told them once" state. Simple, and it means somebody who is later allowed in
is never confused by silence; but a persistent user can make the bot repeat itself. The
message can be set to an empty string to refuse silently.

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

All four middlewares catch every exception, log it, and let the update proceed.
Availability of the bot is prioritized over completeness of the audit trail — if the DB is
down, conversations continue but are not recorded.

## Access control fails open

`AccessMiddleware` follows the same rule: if reading `settings` or the user's status
raises, the update is handled anyway. A database outage therefore degrades to "everyone
gets in" rather than "nobody does". For a bot that gates paid or private content the
opposite default (fail closed) would be right — it is a one-line change in
`telegram_bot/middlewares.py`.

## Settings cached for 5 seconds

The bot re-reads the `settings` table at most every 5 seconds, so blocking a user or
silencing the bot from the admin UI takes effect with that delay instead of instantly. The
alternative — reading on every update, or a Postgres `LISTEN/NOTIFY` channel — costs a
query per update or a second connection per process.

## `requirements.txt` kept alongside `pyproject.toml`

uv + `pyproject.toml` + `uv.lock` is the source of truth; `requirements.txt` is a
convenience mirror for pip-only environments and can drift if only one is updated.

## Single-instance long polling

Polling is simpler than webhooks (no public endpoint, no TLS certs) but caps the
deployment at exactly one instance. Moving to webhooks is the path to horizontal scaling
or zero-downtime deploys. Only the `bot` service is affected — the API does not poll.

## Admin UI reads are un-cached and un-paginated at the top

Every admin page is `force-dynamic` with `cache: "no-store"`, and the user list fetches up
to 100 rows at once with no pagination controls (the API supports `limit`/`offset`; only
the message log uses them). Always-fresh data is the right default for an ops panel at this
size; a few thousand users would call for real paging and some caching.

## Full raw payloads stored forever

Every update and API call is stored as JSONB with no retention policy. Cheap now; at
scale this table grows unboundedly and may accumulate personal data that warrants a
retention/cleanup policy.
