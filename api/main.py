import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import require_api_key
from api.routers import access, bot, messages, users
from core.config import CORS_ORIGINS, DATABASE_URL
from core.db import create_pool
from telegram_bot.main import build_bot

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool(DATABASE_URL)
    # Same Bot wiring as the poller, so messages sent through the API land in the
    # message log too. It never polls — it only makes outgoing calls.
    app.state.bot = build_bot(app.state.pool)
    try:
        yield
    finally:
        await app.state.bot.session.close()
        await app.state.pool.close()


app = FastAPI(
    title="ChickenBot API",
    version="0.1.0",
    description="Control the Telegram bot, manage who may use it, and read/send messages.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Unauthenticated liveness probe — also verifies the DB round-trips."""
    try:
        await app.state.pool.fetchval("SELECT 1")
    except Exception as exc:
        logger.warning("Health check failed: %s", exc)
        return {"status": "degraded", "database": "unavailable"}
    return {"status": "ok", "database": "ok"}


for router in (bot.router, users.router, access.router, messages.router):
    app.include_router(router, prefix="/api", dependencies=[Depends(require_api_key)])
