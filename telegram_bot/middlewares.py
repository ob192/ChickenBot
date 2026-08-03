import logging
import time
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
from aiogram.types import Message, TelegramObject, Update

from core.db import get_access_status, get_settings, log_message, upsert_user

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


class AccessMiddleware(BaseMiddleware):
    """Drops updates from users who may not use the bot, and while the bot is off.

    The two knobs live in the `settings` table and are managed through the API:

    - `bot_enabled`  — 'false' silences the bot entirely (updates are still logged).
    - `access_mode`  — 'open' lets everyone through except explicitly blocked users;
                       'allowlist' lets only `access_status = 'allowed'` users through.
    """

    #: seconds a fetched settings snapshot is reused before re-reading the table
    SETTINGS_TTL = 5.0

    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool
        self._settings: dict[str, str] = {}
        self._settings_read_at = 0.0

    async def _current_settings(self) -> dict[str, str]:
        now = time.monotonic()
        if not self._settings or now - self._settings_read_at > self.SETTINGS_TTL:
            self._settings = await get_settings(self.pool)
            self._settings_read_at = now
        return self._settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            settings = await self._current_settings()
            user = data.get("event_from_user")
            status = (
                await get_access_status(self.pool, user.id) if user else None
            ) or "pending"
        except Exception:
            # Fail open: a settings/DB hiccup must not take the bot down.
            logger.exception("Access check failed, letting the update through")
            return await handler(event, data)

        if settings.get("bot_enabled", "true") != "true":
            return None

        allowed = (
            status != "blocked"
            if settings.get("access_mode") == "open"
            else status == "allowed"
        )
        if allowed:
            data["access_status"] = status
            return await handler(event, data)

        # Tell the person why nothing happens — but only for plain messages, so
        # we don't spam on every callback/edit an unauthorized user produces.
        message = getattr(event, "event", None)
        denied = settings.get("access_denied_message", "")
        if denied and isinstance(message, Message):
            try:
                await message.answer(denied)
            except Exception:
                logger.exception(
                    "Failed to send access-denied reply to %s",
                    user.id if user else "unknown sender",
                )
        return None


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
