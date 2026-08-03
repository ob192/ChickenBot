from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

import asyncpg
from aiogram.types import User

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

# access_status: 'pending'  — seen but never decided on
#                'allowed'  — explicitly granted access
#                'blocked'  — explicitly denied access
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id       BIGINT PRIMARY KEY,
    username          TEXT,
    first_name        TEXT NOT NULL,
    last_name         TEXT,
    language_code     TEXT,
    is_premium        BOOLEAN NOT NULL DEFAULT FALSE,
    first_seen_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    access_status     TEXT NOT NULL DEFAULT 'pending'
                      CHECK (access_status IN ('pending', 'allowed', 'blocked')),
    access_note       TEXT,
    access_updated_at TIMESTAMPTZ
)
"""

# The users table predates access control, so bring existing deployments forward.
ALTER_USERS_ACCESS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS access_status TEXT NOT NULL DEFAULT 'pending'",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS access_note TEXT",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS access_updated_at TIMESTAMPTZ",
]

CREATE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id                  BIGSERIAL PRIMARY KEY,
    direction           TEXT NOT NULL CHECK (direction IN ('in', 'out')),
    chat_id             BIGINT,
    user_id             BIGINT,
    event_type          TEXT NOT NULL,
    text                TEXT,
    telegram_message_id BIGINT,
    payload             JSONB NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

CREATE_MESSAGES_INDEX = """
CREATE INDEX IF NOT EXISTS messages_chat_created_idx
    ON messages (chat_id, created_at)
"""

# Runtime knobs the API can flip without redeploying the bot.
CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

DEFAULT_SETTINGS = {
    # 'true' / 'false' — when false the bot ignores every incoming update
    "bot_enabled": "true",
    # 'open'      — everyone may talk to the bot except blocked users
    # 'allowlist' — only users with access_status = 'allowed' may talk to the bot
    "access_mode": "open",
    "access_denied_message": "Sorry, you don't have access to this bot.",
}

SEED_SETTING = """
INSERT INTO settings (key, value) VALUES ($1, $2)
ON CONFLICT (key) DO NOTHING
"""

# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

INSERT_MESSAGE = """
INSERT INTO messages (direction, chat_id, user_id, event_type, text, telegram_message_id, payload)
VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
"""

UPSERT_USER = """
INSERT INTO users (telegram_id, username, first_name, last_name, language_code, is_premium)
VALUES ($1, $2, $3, $4, $5, $6)
ON CONFLICT (telegram_id) DO UPDATE SET
    username      = EXCLUDED.username,
    first_name    = EXCLUDED.first_name,
    last_name     = EXCLUDED.last_name,
    language_code = EXCLUDED.language_code,
    is_premium    = EXCLUDED.is_premium,
    last_seen_at  = now()
"""

SELECT_ACCESS_STATUS = "SELECT access_status FROM users WHERE telegram_id = $1"

SELECT_SETTINGS = "SELECT key, value FROM settings"

UPSERT_SETTING = """
INSERT INTO settings (key, value) VALUES ($1, $2)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()
"""

USER_COLUMNS = """
    telegram_id, username, first_name, last_name, language_code, is_premium,
    first_seen_at, last_seen_at, access_status, access_note, access_updated_at
"""

SELECT_USER = f"SELECT {USER_COLUMNS} FROM users WHERE telegram_id = $1"

SET_USER_ACCESS = f"""
UPDATE users
   SET access_status = $2, access_note = $3, access_updated_at = now()
 WHERE telegram_id = $1
RETURNING {USER_COLUMNS}
"""

# Pre-authorize somebody who has never messaged the bot: creates a stub row that
# the bot's own upsert fills in with the real profile on first contact.
PREAUTHORIZE_USER = f"""
INSERT INTO users (telegram_id, username, first_name, access_status, access_note, access_updated_at)
VALUES ($1, $2, $3, $4, $5, now())
ON CONFLICT (telegram_id) DO UPDATE SET
    access_status     = EXCLUDED.access_status,
    access_note       = EXCLUDED.access_note,
    access_updated_at = now()
RETURNING {USER_COLUMNS}
"""

COUNT_USERS_BY_STATUS = "SELECT access_status, count(*) AS total FROM users GROUP BY access_status"

COUNT_MESSAGES = """
SELECT count(*) FILTER (WHERE direction = 'in')  AS incoming,
       count(*) FILTER (WHERE direction = 'out') AS outgoing
FROM messages
"""

SELECT_MESSAGES_FOR_CHAT = """
SELECT id, direction, chat_id, user_id, event_type, text, telegram_message_id, created_at
FROM messages
WHERE chat_id = $1
ORDER BY created_at DESC, id DESC
LIMIT $2 OFFSET $3
"""

SELECT_RECENT_MESSAGES = """
SELECT id, direction, chat_id, user_id, event_type, text, telegram_message_id, created_at
FROM messages
ORDER BY created_at DESC, id DESC
LIMIT $1 OFFSET $2
"""


def _clean_dsn(dsn: str) -> str:
    # asyncpg does not understand the channel_binding query param (Neon adds it
    # for libpq clients), so strip it before connecting.
    parts = urlparse(dsn)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k != "channel_binding"]
    return urlunparse(parts._replace(query=urlencode(query)))


async def create_pool(dsn: str) -> asyncpg.Pool:
    pool = await asyncpg.create_pool(_clean_dsn(dsn), min_size=1, max_size=5)
    async with pool.acquire() as conn:
        await conn.execute(CREATE_USERS_TABLE)
        for statement in ALTER_USERS_ACCESS:
            await conn.execute(statement)
        await conn.execute(CREATE_MESSAGES_TABLE)
        await conn.execute(CREATE_MESSAGES_INDEX)
        await conn.execute(CREATE_SETTINGS_TABLE)
        for key, value in DEFAULT_SETTINGS.items():
            await conn.execute(SEED_SETTING, key, value)
    return pool


# ---------------------------------------------------------------------------
# Message log
# ---------------------------------------------------------------------------


async def log_message(
    pool: asyncpg.Pool,
    *,
    direction: str,
    chat_id: int | None,
    user_id: int | None,
    event_type: str,
    text: str | None,
    telegram_message_id: int | None,
    payload: str,
) -> None:
    await pool.execute(
        INSERT_MESSAGE,
        direction,
        chat_id,
        user_id,
        event_type,
        text,
        telegram_message_id,
        payload,
    )


async def messages_for_chat(
    pool: asyncpg.Pool, chat_id: int, *, limit: int, offset: int
) -> list[asyncpg.Record]:
    return await pool.fetch(SELECT_MESSAGES_FOR_CHAT, chat_id, limit, offset)


async def recent_messages(
    pool: asyncpg.Pool, *, limit: int, offset: int
) -> list[asyncpg.Record]:
    return await pool.fetch(SELECT_RECENT_MESSAGES, limit, offset)


# ---------------------------------------------------------------------------
# Users & access
# ---------------------------------------------------------------------------


async def upsert_user(pool: asyncpg.Pool, user: User) -> None:
    await pool.execute(
        UPSERT_USER,
        user.id,
        user.username,
        user.first_name,
        user.last_name,
        user.language_code,
        bool(user.is_premium),
    )


async def get_user(pool: asyncpg.Pool, telegram_id: int) -> asyncpg.Record | None:
    return await pool.fetchrow(SELECT_USER, telegram_id)


async def get_access_status(pool: asyncpg.Pool, telegram_id: int) -> str | None:
    return await pool.fetchval(SELECT_ACCESS_STATUS, telegram_id)


async def set_user_access(
    pool: asyncpg.Pool, telegram_id: int, status: str, note: str | None
) -> asyncpg.Record | None:
    return await pool.fetchrow(SET_USER_ACCESS, telegram_id, status, note)


async def preauthorize_user(
    pool: asyncpg.Pool,
    telegram_id: int,
    *,
    status: str,
    username: str | None,
    first_name: str,
    note: str | None,
) -> asyncpg.Record:
    return await pool.fetchrow(
        PREAUTHORIZE_USER, telegram_id, username, first_name, status, note
    )


async def list_users(
    pool: asyncpg.Pool,
    *,
    status: str | None = None,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[asyncpg.Record], int]:
    """Returns a page of users (most recently active first) and the total count."""
    where: list[str] = []
    args: list[object] = []

    if status:
        args.append(status)
        where.append(f"access_status = ${len(args)}")
    if query:
        args.append(f"%{query}%")
        placeholder = f"${len(args)}"
        where.append(
            "(username ILIKE {p} OR first_name ILIKE {p} OR last_name ILIKE {p}"
            " OR telegram_id::text ILIKE {p})".format(p=placeholder)
        )

    clause = f" WHERE {' AND '.join(where)}" if where else ""
    total = await pool.fetchval(f"SELECT count(*) FROM users{clause}", *args)
    rows = await pool.fetch(
        f"SELECT {USER_COLUMNS} FROM users{clause}"
        f" ORDER BY last_seen_at DESC LIMIT ${len(args) + 1} OFFSET ${len(args) + 2}",
        *args,
        limit,
        offset,
    )
    return rows, total


async def user_counts(pool: asyncpg.Pool) -> dict[str, int]:
    rows = await pool.fetch(COUNT_USERS_BY_STATUS)
    counts = {"pending": 0, "allowed": 0, "blocked": 0}
    for row in rows:
        counts[row["access_status"]] = row["total"]
    counts["total"] = sum(counts.values())
    return counts


async def message_counts(pool: asyncpg.Pool) -> dict[str, int]:
    row = await pool.fetchrow(COUNT_MESSAGES)
    return {
        "incoming": row["incoming"],
        "outgoing": row["outgoing"],
        "total": row["incoming"] + row["outgoing"],
    }


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


async def get_settings(pool: asyncpg.Pool) -> dict[str, str]:
    rows = await pool.fetch(SELECT_SETTINGS)
    return {**DEFAULT_SETTINGS, **{row["key"]: row["value"] for row in rows}}


async def set_setting(pool: asyncpg.Pool, key: str, value: str) -> None:
    await pool.execute(UPSERT_SETTING, key, value)
