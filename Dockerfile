FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install dependencies first so this layer is cached across code changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .

# One image, two entry points: the bot is the default, the API overrides CMD
# (see docker-compose.yml / `make up-api`).
CMD ["uv", "run", "--no-sync", "python", "-m", "telegram_bot.main"]
