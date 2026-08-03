import logging

from fastapi import APIRouter

from api.deps import OptionalTelegramBot, Pool
from api.schemas import BotIdentity, BotSettings, BotSettingsUpdate, BotStatus
from core.db import get_settings, message_counts, set_setting, user_counts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bot", tags=["bot"])


def _to_settings(raw: dict[str, str]) -> BotSettings:
    return BotSettings(
        enabled=raw.get("bot_enabled", "true") == "true",
        access_mode=raw.get("access_mode", "open"),
        access_denied_message=raw.get("access_denied_message", ""),
    )


async def _identity(bot: OptionalTelegramBot) -> BotIdentity:
    if bot is None:
        return BotIdentity(
            id=0, reachable=False, error="TELEGRAM_BOT_TOKEN is not configured"
        )
    try:
        me = await bot.get_me()
    except Exception as exc:  # network / invalid token / Telegram outage
        logger.warning("getMe failed: %s", exc)
        return BotIdentity(id=0, reachable=False, error=str(exc))
    return BotIdentity(
        id=me.id, username=me.username, first_name=me.first_name, reachable=True
    )


@router.get("/status", response_model=BotStatus)
async def bot_status(pool: Pool, bot: OptionalTelegramBot) -> BotStatus:
    """Everything the dashboard needs: runtime switches, identity and counters."""
    return BotStatus(
        settings=_to_settings(await get_settings(pool)),
        identity=await _identity(bot),
        users=await user_counts(pool),
        messages=await message_counts(pool),
    )


@router.get("/settings", response_model=BotSettings)
async def read_settings(pool: Pool) -> BotSettings:
    return _to_settings(await get_settings(pool))


@router.patch("/settings", response_model=BotSettings)
async def update_settings(payload: BotSettingsUpdate, pool: Pool) -> BotSettings:
    """Flip the bot on/off or change the access policy. Takes effect within seconds."""
    if payload.enabled is not None:
        await set_setting(pool, "bot_enabled", "true" if payload.enabled else "false")
    if payload.access_mode is not None:
        await set_setting(pool, "access_mode", payload.access_mode)
    if payload.access_denied_message is not None:
        await set_setting(pool, "access_denied_message", payload.access_denied_message)
    return _to_settings(await get_settings(pool))
