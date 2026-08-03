# Deployment

Three processes make up the stack:

| Service | What it is                | Port |
| ------- | ------------------------- | ---- |
| `bot`   | aiogram long-polling loop | —    |
| `api`   | FastAPI + uvicorn         | 8000 |
| `admin` | Next.js admin UI          | 3000 |

`bot` and `api` are the **same image** with a different command; `admin` has its own.

## Docker images

[`Dockerfile`](../Dockerfile) — based on `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`:

- Dependencies are installed from `uv.lock` (`uv sync --frozen --no-dev`) in their own
  layer, so code-only changes rebuild in seconds.
- `.dockerignore` keeps `.git`, `.venv`, `admin/` and all `.env*` files out of the image —
  it contains **no secrets**; config is injected at runtime.
- Default command: `uv run --no-sync python -m telegram_bot.main`. The API service
  overrides it with `uv run --no-sync uvicorn api.main:app --host 0.0.0.0 --port 8000`.

[`admin/Dockerfile`](../admin/Dockerfile) — multi-stage `node:22-bookworm-slim`: install,
`next build`, then a runtime stage with only production `node_modules` and `.next`.
`API_BASE_URL` / `API_KEY` are injected at runtime, never baked in.

Image names: **`sasha192bunin/chickenbot`** and **`sasha192bunin/chickenbot-admin`**.

## Compose

[`docker-compose.yml`](../docker-compose.yml) runs all three. The admin container reaches
the API by service name (`http://api:8000`), so only ports 8000 and 3000 are published.
`API_KEY` must be present in the env file — compose refuses to start without it.

```bash
make dev    # build + run everything in the foreground
make up     # same, detached, then follow logs
make stop   # docker compose down
```

## Makefile targets

[`Makefile`](../Makefile):

| Target             | What it does                                                        |
| ------------------ | ------------------------------------------------------------------- |
| `make bot`         | Run the bot locally with uv (`make run` is an alias)                |
| `make api`         | Run FastAPI locally with auto-reload on :8000                       |
| `make admin`       | Run the Next.js dev server on :3000                                 |
| `make dev`         | `docker compose up --build` — the whole stack                       |
| `make build`       | Build the python image (bot + api)                                  |
| `make build-admin` | Build the admin UI image                                            |
| `make deploy`      | Build and push both images to Docker Hub                            |
| `make up` / `stop` | Start the stack detached / tear it down                             |
| `make logs`        | Follow logs of all services                                         |

Variables can be overridden per invocation, e.g. `make up ENV_FILE=.env.local` or
`make deploy TAG=v2`.

## Running on a server

```bash
docker compose --env-file .env up -d
```

The `.env` file on the server must define `TELEGRAM_BOT_TOKEN`, `DATABASE_URL` and
`API_KEY`. Or run the bot alone, as before:

```bash
docker run -d --name chickenbot --restart unless-stopped \
  --env-file .env sasha192bunin/chickenbot:latest
```

## Constraints

- The bot uses **long polling**, so exactly **one `bot` instance** may run at a time — two
  instances polling the same token will fight over updates. The API service does not poll,
  so it can be scaled independently.
- Expose the API and the admin UI carefully: the API key is the only thing protecting them,
  and the admin UI has no login of its own. Localhost, a VPN, or an authenticating reverse
  proxy — see [CONCESSIONS.md](../CONCESSIONS.md).
- Pushing to Docker Hub requires `docker login` as `sasha192bunin`.
- `make deploy` publishes the *local* code — remember to run it after changes, or the
  Docker Hub images lag behind the repo.
