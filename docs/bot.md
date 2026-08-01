# Bot runtime

## Entry point

[`main.py`](../main.py) wires everything together:

1. Creates the asyncpg connection pool (which also creates missing tables — see
   [database.md](database.md)).
2. Creates the `Bot` and attaches `LogOutgoingMiddleware` to its HTTP session.
3. Creates the `Dispatcher`, attaches `StoreUserMiddleware` and `LogIncomingMiddleware`
   as outer middlewares on **all** updates, and includes the handler router.
4. Starts long polling. The pool is closed on shutdown.

## Update flow

```
Telegram ──update──▶ Dispatcher
                       │ StoreUserMiddleware      upsert sender into users
                       │ LogIncomingMiddleware    insert update into messages (direction='in')
                       ▼
                    handlers.py                   business logic
                       │ bot.send_message(...)
                       ▼
                    Bot session
                       │ LogOutgoingMiddleware    insert API call into messages (direction='out')
                       ▼
                    Telegram API
```

Both dispatcher middlewares are **outer** middlewares: they run for every incoming update,
including ones no handler handles. Both swallow their own database errors (logged with
stack trace) so a DB hiccup never prevents the bot from answering.

## Handlers

[`bot/handlers.py`](../bot/handlers.py) — a single aiogram `Router`.

| Trigger  | Response                                  |
| -------- | ----------------------------------------- |
| `/start` | "Hello! ChickenBot is up and running."    |

Everything else is ignored (but still recorded by the middlewares).

## Middlewares

[`bot/middlewares.py`](../bot/middlewares.py):

- **`StoreUserMiddleware`** — upserts `event_from_user` into `users` on every update;
  skips bots.
- **`LogIncomingMiddleware`** — serializes the whole `Update` to JSONB and inserts it into
  `messages` with extracted chat id, user id, event type (`message`, `callback_query`, …),
  text (text / caption / callback data), and Telegram message id.
- **`LogOutgoingMiddleware`** — a *session* middleware (`BaseRequestMiddleware`), so it sees
  every Bot API call regardless of which handler made it. Calls with an integer `chat_id`
  (sendMessage, sendPhoto, editMessageText, …) are recorded with `direction='out'`;
  everything else (getUpdates polling, etc.) is skipped.

## Game assets

`chiken/` holds numbered images for Easy / Medium / Hard modes. They are **not used by any
code yet** — the game logic is still to be designed (see [ISSUES.md](../ISSUES.md)).
