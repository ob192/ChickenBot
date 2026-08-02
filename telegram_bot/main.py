import asyncio
import logging

import asyncpg
from aiogram import Bot, Dispatcher

from core.config import BOT_TOKEN, DATABASE_URL
from core.db import create_pool
from telegram_bot.handlers import router
from telegram_bot.middlewares import (
    AccessMiddleware,
    LogIncomingMiddleware,
    LogOutgoingMiddleware,
    StoreUserMiddleware,
)


def build_bot(pool: asyncpg.Pool | None = None, token: str = BOT_TOKEN) -> Bot:
    """A Bot whose outgoing calls are logged — shared by the poller and the API."""
    bot = Bot(token=token)
    if pool is not None:
        bot.session.middleware(LogOutgoingMiddleware(pool))
    return bot


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    pool = await create_pool(DATABASE_URL)

    bot = build_bot(pool)
    dp = Dispatcher()
    # Order matters: store the sender, log the raw update, then enforce access.
    dp.update.outer_middleware(StoreUserMiddleware(pool))
    dp.update.outer_middleware(LogIncomingMiddleware(pool))
    dp.update.outer_middleware(AccessMiddleware(pool))
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
