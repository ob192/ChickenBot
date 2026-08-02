from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from api.deps import Pool
from api.schemas import (
    AccessStatus,
    AccessUpdate,
    LoggedMessage,
    MessagePage,
    User,
    UserPage,
)
from core.db import get_user, list_users, messages_for_chat, set_user_access

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserPage)
async def list_bot_users(
    pool: Pool,
    status_filter: Annotated[AccessStatus | None, Query(alias="status")] = None,
    query: Annotated[str | None, Query(description="Match id, username or name")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserPage:
    rows, total = await list_users(
        pool, status=status_filter, query=query, limit=limit, offset=offset
    )
    return UserPage(
        items=[User(**dict(row)) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{telegram_id}", response_model=User)
async def read_user(telegram_id: int, pool: Pool) -> User:
    row = await get_user(pool, telegram_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return User(**dict(row))


@router.patch("/{telegram_id}/access", response_model=User)
async def update_user_access(
    telegram_id: int, payload: AccessUpdate, pool: Pool
) -> User:
    """Allow / block / reset a user the bot has already seen."""
    row = await set_user_access(pool, telegram_id, payload.status, payload.note)
    if row is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "User not found — use POST /api/access/grants to pre-authorize an id",
        )
    return User(**dict(row))


@router.get("/{telegram_id}/messages", response_model=MessagePage)
async def read_user_messages(
    telegram_id: int,
    pool: Pool,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MessagePage:
    """The conversation with one user, newest first (private chat id == user id)."""
    rows = await messages_for_chat(pool, telegram_id, limit=limit, offset=offset)
    return MessagePage(
        items=[LoggedMessage(**dict(row)) for row in rows], limit=limit, offset=offset
    )
