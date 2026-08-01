import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import BOT_TOKEN, DATABASE_URL
from bot.db import create_pool
from bot.handlers import router
from bot.middlewares import (
    LogIncomingMiddleware,
    LogOutgoingMiddleware,
    StoreUserMiddleware,
)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    pool = await create_pool(DATABASE_URL)

    bot = Bot(token=BOT_TOKEN)
    bot.session.middleware(LogOutgoingMiddleware(pool))
    dp = Dispatcher()
    dp.update.outer_middleware(StoreUserMiddleware(pool))
    dp.update.outer_middleware(LogIncomingMiddleware(pool))
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
