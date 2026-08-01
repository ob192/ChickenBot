from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

import asyncpg
from aiogram.types import User

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id   BIGINT PRIMARY KEY,
    username      TEXT,
    first_name    TEXT NOT NULL,
    last_name     TEXT,
    language_code TEXT,
    is_premium    BOOLEAN NOT NULL DEFAULT FALSE,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

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
        await conn.execute(CREATE_MESSAGES_TABLE)
        await conn.execute(CREATE_MESSAGES_INDEX)
    return pool


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
