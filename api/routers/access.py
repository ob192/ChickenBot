from fastapi import APIRouter, HTTPException, status

from api.deps import Pool
from api.schemas import (
    AccessGrant,
    AccessOverview,
    AccessSettings,
    AccessSettingsUpdate,
    User,
)
from core.db import (
    get_settings,
    get_user,
    preauthorize_user,
    set_setting,
    set_user_access,
    user_counts,
)

router = APIRouter(prefix="/access", tags=["access"])


def _to_settings(raw: dict[str, str]) -> AccessSettings:
    return AccessSettings(
        access_mode=raw.get("access_mode", "open"),
        access_denied_message=raw.get("access_denied_message", ""),
    )


@router.get("", response_model=AccessOverview)
async def access_overview(pool: Pool) -> AccessOverview:
    """Current policy plus how many users sit in each access bucket."""
    return AccessOverview(
        settings=_to_settings(await get_settings(pool)), users=await user_counts(pool)
    )


@router.patch("/settings", response_model=AccessSettings)
async def update_access_settings(
    payload: AccessSettingsUpdate, pool: Pool
) -> AccessSettings:
    if payload.access_mode is not None:
        await set_setting(pool, "access_mode", payload.access_mode)
    if payload.access_denied_message is not None:
        await set_setting(pool, "access_denied_message", payload.access_denied_message)
    return _to_settings(await get_settings(pool))


@router.post("/grants", response_model=User, status_code=status.HTTP_201_CREATED)
async def grant_access(payload: AccessGrant, pool: Pool) -> User:
    """Allow (or block) a Telegram id up front, before that person ever writes.

    Creates a placeholder user row; the bot fills in the real profile on first contact.
    """
    row = await preauthorize_user(
        pool,
        payload.telegram_id,
        status=payload.status,
        username=payload.username,
        first_name=payload.first_name,
        note=payload.note,
    )
    return User(**dict(row))


@router.delete("/grants/{telegram_id}", response_model=User)
async def revoke_access(telegram_id: int, pool: Pool) -> User:
    """Reset a user back to 'pending' (kept in the DB, keeps their message history)."""
    if await get_user(pool, telegram_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    row = await set_user_access(pool, telegram_id, "pending", None)
    return User(**dict(row))
