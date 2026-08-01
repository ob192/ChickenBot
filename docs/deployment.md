# Deployment

## Docker image

[`Dockerfile`](../Dockerfile) is based on `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`:

- Dependencies are installed from `uv.lock` (`uv sync --frozen --no-dev`) in their own
  layer, so code-only changes rebuild in seconds.
- `.dockerignore` keeps `.git`, `.venv`, and all `.env*` files out of the image — the image
  contains **no secrets**; config is injected at runtime.
- Entry point: `uv run --no-sync python main.py`.

Image name: **`sasha192bunin/chickenbot`** on Docker Hub.

## Makefile targets

[`Makefile`](../Makefile):

| Target        | What it does                                                            |
| ------------- | ----------------------------------------------------------------------- |
| `make run`    | Run locally with uv (no Docker)                                         |
| `make build`  | `docker build -t sasha192bunin/chickenbot:latest .`                     |
| `make deploy` | `build` + `docker push` to Docker Hub                                   |
| `make up`     | Replace + start the container (`--restart unless-stopped`, `--env-file .env`), then tail logs |
| `make stop`   | Remove the container                                                    |
| `make logs`   | Follow container logs                                                   |

Variables can be overridden per invocation, e.g. `make up ENV_FILE=.env.local` or
`make deploy TAG=v2`.

## Running on a server

```bash
docker run -d \
  --name chickenbot \
  --restart unless-stopped \
  --env-file .env \
  sasha192bunin/chickenbot:latest
```

The `.env` file on the server must define `TELEGRAM_BOT_TOKEN` and `DATABASE_URL`.

## Constraints

- The bot uses **long polling**, so exactly **one instance** may run at a time — two
  instances polling the same token will fight over updates. Stop the old container before
  starting a new one (`make up` does this).
- Pushing to Docker Hub requires `docker login` as `sasha192bunin`.
- `make deploy` publishes the *local* code — remember to run it after changes, or the
  Docker Hub image lags behind the repo.
