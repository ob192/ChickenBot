import secrets
from typing import Annotated

import asyncpg
from aiogram import Bot
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from core.config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: Annotated[str | None, Depends(api_key_header)]) -> None:
    if not API_KEY:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "API_KEY is not configured on the server",
        )
    if not key or not secrets.compare_digest(key, API_KEY):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing API key")


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


def get_optional_bot(request: Request) -> Bot | None:
    """None when TELEGRAM_BOT_TOKEN is missing — the API still runs without it."""
    return request.app.state.bot


def get_bot(request: Request) -> Bot:
    bot = request.app.state.bot
    if bot is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "TELEGRAM_BOT_TOKEN is not configured — the API cannot talk to Telegram",
        )
    return bot


Pool = Annotated[asyncpg.Pool, Depends(get_pool)]
TelegramBot = Annotated[Bot, Depends(get_bot)]
OptionalTelegramBot = Annotated[Bot | None, Depends(get_optional_bot)]
