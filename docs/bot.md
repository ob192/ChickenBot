# Bot runtime

The Telegram bot lives in [`telegram_bot/`](../telegram_bot) and shares the database layer
in [`core/`](../core) with the [API](api.md).

## Entry point

[`telegram_bot/main.py`](../telegram_bot/main.py) wires everything together:

1. Creates the asyncpg connection pool (which also creates missing tables — see
   [database.md](database.md)).
2. Builds the `Bot` via `build_bot()`, which attaches `LogOutgoingMiddleware` to its HTTP
   session. The API reuses this same helper so its sends are logged identically.
3. Creates the `Dispatcher`, attaches `StoreUserMiddleware`, `LogIncomingMiddleware` and
   `AccessMiddleware` as outer middlewares on **all** updates, and includes the router.
4. Starts long polling. The pool is closed on shutdown.

Run it with `make bot` (`uv run python -m telegram_bot.main`).

## Update flow

```
Telegram ──update──▶ Dispatcher
                       │ StoreUserMiddleware      upsert sender into users
                       │ LogIncomingMiddleware    insert update into messages (direction='in')
                       │ AccessMiddleware         drop it if the bot is off or access denied
                       ▼
                    handlers.py                   business logic
                       │ bot.send_message(...)
                       ▼
                    Bot session
                       │ LogOutgoingMiddleware    insert API call into messages (direction='out')
                       ▼
                    Telegram API
```

All three dispatcher middlewares are **outer** middlewares: they run for every incoming
update, including ones no handler handles. Storing and logging happen *before* the access
check, so refused updates are still recorded. All of them swallow their own database errors
(logged with stack trace) so a DB hiccup never prevents the bot from answering.

## Handlers

[`telegram_bot/handlers.py`](../telegram_bot/handlers.py) — a single aiogram `Router`.

| Trigger  | Response                                  |
| -------- | ----------------------------------------- |
| `/start` | "Hello! ChickenBot is up and running."    |

Everything else is ignored (but still recorded by the middlewares).

## Middlewares

[`telegram_bot/middlewares.py`](../telegram_bot/middlewares.py):

- **`StoreUserMiddleware`** — upserts `event_from_user` into `users` on every update;
  skips bots.
- **`LogIncomingMiddleware`** — serializes the whole `Update` to JSONB and inserts it into
  `messages` with extracted chat id, user id, event type (`message`, `callback_query`, …),
  text (text / caption / callback data), and Telegram message id.
- **`AccessMiddleware`** — enforces the `bot_enabled` kill switch and the access policy,
  re-reading `settings` at most every 5 seconds. Fails open on database errors. Full
  behaviour in [access-control.md](access-control.md).
- **`LogOutgoingMiddleware`** — a *session* middleware (`BaseRequestMiddleware`), so it sees
  every Bot API call regardless of which handler — or which process — made it. Calls with an
  integer `chat_id` (sendMessage, sendPhoto, editMessageText, …) are recorded with
  `direction='out'`; everything else (getUpdates polling, etc.) is skipped.

## Game assets

`chiken/` holds numbered images for Easy / Medium / Hard modes. They are **not used by any
code yet** — the game logic is still to be designed (see [ISSUES.md](../ISSUES.md)).
