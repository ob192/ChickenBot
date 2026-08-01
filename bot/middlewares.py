import logging
from collections.abc import Awaitable, Callable
from typing import Any

import asyncpg
from aiogram import BaseMiddleware, Bot
from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.methods import TelegramMethod
from aiogram.methods.base import Response, TelegramType
from aiogram.types import TelegramObject, Update

from bot.db import log_message, upsert_user

logger = logging.getLogger(__name__)


def _extract_text(event: Any) -> str | None:
    for attr in ("text", "caption", "data", "query"):
        value = getattr(event, attr, None)
        if isinstance(value, str) and value:
            return value
    return None


class StoreUserMiddleware(BaseMiddleware):
    """Upserts the sender of every incoming update into the users table."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None and not user.is_bot:
            try:
                await upsert_user(self.pool, user)
            except Exception:
                logger.exception("Failed to store user %s", user.id)
        return await handler(event, data)


class LogIncomingMiddleware(BaseMiddleware):
    """Stores every incoming update (messages, callbacks, etc.) in the messages table."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            try:
                user = data.get("event_from_user")
                chat = data.get("event_chat")
                inner = event.event
                await log_message(
                    self.pool,
                    direction="in",
                    chat_id=chat.id if chat else None,
                    user_id=user.id if user else None,
                    event_type=event.event_type,
                    text=_extract_text(inner),
                    telegram_message_id=getattr(inner, "message_id", None),
                    payload=event.model_dump_json(exclude_none=True),
                )
            except Exception:
                logger.exception("Failed to log incoming update %s", event.update_id)
        return await handler(event, data)


class LogOutgoingMiddleware(BaseRequestMiddleware):
    """Stores every chat-directed API call the bot makes in the messages table."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        response = await make_request(bot, method)
        chat_id = getattr(method, "chat_id", None)
        # Only chat-directed calls (sendMessage, sendPhoto, editMessageText, ...);
        # skips polling noise like getUpdates.
        if isinstance(chat_id, int):
            try:
                result = response.result
                message_id = getattr(result, "message_id", None)
                await log_message(
                    self.pool,
                    direction="out",
                    chat_id=chat_id,
                    # In private chats the chat id is the user id
                    user_id=chat_id if chat_id > 0 else None,
                    event_type=method.__api_method__,
                    text=_extract_text(method),
                    telegram_message_id=message_id,
                    # fallback drops aiogram's unset-value Default sentinels
                    payload=method.model_dump_json(
                        exclude_none=True, fallback=lambda _: None
                    ),
                )
            except Exception:
                logger.exception("Failed to log outgoing %s", method.__api_method__)
        return response
