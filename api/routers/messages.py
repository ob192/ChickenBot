import logging
from datetime import datetime, timezone
from typing import Annotated

from aiogram.exceptions import TelegramAPIError
from fastapi import APIRouter, HTTPException, Query, status

from api.deps import Pool, TelegramBot
from api.schemas import (
    LoggedMessage,
    MessagePage,
    SendMessageRequest,
    SendMessageResponse,
)
from core.db import get_access_status, get_settings, recent_messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=MessagePage)
async def list_messages(
    pool: Pool,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MessagePage:
    """The global conversation log, newest first."""
    rows = await recent_messages(pool, limit=limit, offset=offset)
    return MessagePage(
        items=[LoggedMessage(**dict(row)) for row in rows], limit=limit, offset=offset
    )


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    payload: SendMessageRequest, pool: Pool, bot: TelegramBot
) -> SendMessageResponse:
    """Send a message as the bot. Logged like any other outgoing call.

    Refuses recipients the access policy excludes unless `force` is set, so the
    admin UI can't accidentally talk to someone who was just blocked.
    """
    if not payload.force and payload.chat_id > 0:
        settings = await get_settings(pool)
        access = await get_access_status(pool, payload.chat_id) or "pending"
        allowed = (
            access != "blocked"
            if settings.get("access_mode") == "open"
            else access == "allowed"
        )
        if not allowed:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"User {payload.chat_id} has access_status '{access}' under "
                f"access_mode '{settings.get('access_mode')}'; pass force=true to override",
            )

    try:
        sent = await bot.send_message(chat_id=payload.chat_id, text=payload.text)
    except TelegramAPIError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Telegram: {exc}") from exc

    return SendMessageResponse(
        telegram_message_id=sent.message_id,
        chat_id=payload.chat_id,
        sent_at=sent.date or datetime.now(timezone.utc),
    )
