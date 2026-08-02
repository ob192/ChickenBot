# API

A [FastAPI](https://fastapi.tiangolo.com/) service that is the control plane for the bot:
it flips runtime switches, decides who may talk to the bot, exposes the conversation log
and sends messages as the bot.

Run it locally with `make api` — interactive docs at <http://localhost:8000/docs>.

## Layout

```
api/main.py            app factory, lifespan (pool + Bot), CORS, /health
api/deps.py            X-API-Key auth, pool/bot dependencies
api/schemas.py         pydantic request/response models
api/routers/bot.py     runtime switches + status
api/routers/users.py   user list/detail/messages, per-user access
api/routers/access.py  access policy and pre-authorization
api/routers/messages.py global log + send as the bot
```

The service shares [`core/`](../core) with the bot: same pool, same schema, same queries.
It builds its `Bot` through `telegram_bot.main.build_bot()`, so **messages sent through the
API are written to the message log** by the same outgoing middleware the poller uses. The
API never polls — it only makes outgoing calls.

## Authentication

Every `/api/*` route requires the `X-API-Key` header to match the `API_KEY` environment
variable (constant-time comparison). `/health`, `/docs` and `/openapi.json` are open.

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/bot/status
```

Requests without a valid key get `401`; if the server has no `API_KEY` configured every
authenticated route returns `503` rather than silently running unprotected.

## Endpoints

| Method   | Path                             | What it does                                          |
| -------- | -------------------------------- | ----------------------------------------------------- |
| `GET`    | `/health`                        | Liveness + DB round-trip (no auth)                    |
| `GET`    | `/api/bot/status`                | Switches, Telegram identity (`getMe`), user/message counters |
| `GET`    | `/api/bot/settings`              | Current runtime switches                              |
| `PATCH`  | `/api/bot/settings`              | `enabled`, `access_mode`, `access_denied_message`     |
| `GET`    | `/api/users`                     | Paged user list; `status`, `query`, `limit`, `offset` |
| `GET`    | `/api/users/{telegram_id}`       | One user                                              |
| `PATCH`  | `/api/users/{telegram_id}/access`| Set `allowed` / `blocked` / `pending` (+ note)        |
| `GET`    | `/api/users/{telegram_id}/messages` | That chat's history, newest first                  |
| `GET`    | `/api/access`                    | Access policy + counts per bucket                     |
| `PATCH`  | `/api/access/settings`           | Change the policy                                     |
| `POST`   | `/api/access/grants`             | Pre-authorize (or pre-block) a Telegram id            |
| `DELETE` | `/api/access/grants/{telegram_id}` | Reset a user back to `pending`                      |
| `GET`    | `/api/messages`                  | Global log, newest first                              |
| `POST`   | `/api/messages/send`             | Send a message as the bot                             |

See [access-control.md](access-control.md) for what the access fields mean.

## Sending messages

```bash
curl -X POST http://localhost:8000/api/messages/send \
  -H "X-API-Key: $API_KEY" -H 'Content-Type: application/json' \
  -d '{"chat_id": 123456789, "text": "Hello from the API"}'
```

The endpoint refuses recipients the current access policy excludes (`403`) so an operator
cannot accidentally message someone they just blocked; pass `"force": true` to override.
Telegram errors surface as `502` with the Telegram message attached. Successful sends are
logged with `direction='out'` exactly like handler-sent messages.

## Error shape

FastAPI's default: `{"detail": "..."}` with the relevant status code — `401` (bad key),
`403` (access policy), `404` (unknown user), `422` (validation), `502` (Telegram),
`503` (no API key configured).
