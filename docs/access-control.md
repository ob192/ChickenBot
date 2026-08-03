# Access control

Who may talk to the bot is decided by two things: a **global mode** and a **per-user
status**. Both live in Postgres, so the API changes them and the bot picks them up
without a restart.

## Global mode — `settings.access_mode`

| Mode        | Who gets through                                    |
| ----------- | --------------------------------------------------- |
| `open`      | everyone except users with `access_status = 'blocked'` |
| `allowlist` | only users with `access_status = 'allowed'`         |

Default is `open`. Change it with `PATCH /api/access/settings` (or the mode buttons on the
admin dashboard).

## Per-user status — `users.access_status`

| Status    | Meaning                                                           |
| --------- | ----------------------------------------------------------------- |
| `pending` | seen but never decided on (the default for anyone who writes in)  |
| `allowed` | explicitly granted access                                          |
| `blocked` | explicitly denied — never gets through, in either mode             |

`access_note` records *why* (free text) and `access_updated_at` records *when*.

Set it with `PATCH /api/users/{telegram_id}/access`, or pre-authorize an id nobody has seen
yet with `POST /api/access/grants` — that writes a placeholder user row which the bot fills
in with the real profile on first contact. `DELETE /api/access/grants/{telegram_id}` resets
someone to `pending` (the row and its message history stay).

## Enforcement in the bot

[`AccessMiddleware`](../telegram_bot/middlewares.py) is the third outer middleware, so it
runs **after** the user has been stored and the raw update logged: rejected updates are
still recorded, you just never lose the audit trail of who tried.

For each update it:

1. Reads `settings` (cached for 5 s, so a change takes at most ~5 seconds to apply).
2. Returns immediately if `bot_enabled` is `false` — the bot is globally silent.
3. Looks up the sender's `access_status` and applies the mode table above.
4. On refusal, replies with `settings.access_denied_message` — only for plain messages, so
   a rejected user cannot spam themselves through callbacks/edits. Set the message to an
   empty string to refuse silently.

If the settings or status lookup raises, the middleware **fails open** and lets the update
through: a database hiccup degrades access control rather than taking the bot down. Blocked
users are still refused whenever the DB is reachable.

## The kill switch — `settings.bot_enabled`

`PATCH /api/bot/settings {"enabled": false}` silences the bot without stopping the process:
updates keep arriving and keep being logged, but no handler runs and nothing is answered.
Useful for maintenance windows or for stopping an incident without a redeploy.

## API-side enforcement

`POST /api/messages/send` applies the same rules before sending, so the admin UI cannot
message someone the policy excludes unless `force: true` is passed explicitly.

## Common tasks

Everything below is also a button on the admin panel; `$K` is the API key.

Lock the bot down to a handful of people:

```bash
# 1. allow each person (works before they have ever written in)
curl -X POST -H "X-API-Key: $K" -H 'Content-Type: application/json' \
  -d '{"telegram_id": 372096046, "note": "owner"}' \
  http://localhost:8000/api/access/grants

# 2. flip the policy — everyone else is now refused
curl -X PATCH -H "X-API-Key: $K" -H 'Content-Type: application/json' \
  -d '{"access_mode": "allowlist"}' http://localhost:8000/api/access/settings
```

Block one troublesome user but leave the bot open to everyone else:

```bash
curl -X PATCH -H "X-API-Key: $K" -H 'Content-Type: application/json' \
  -d '{"status": "blocked", "note": "spam"}' \
  http://localhost:8000/api/users/6529568076/access
```

Who is waiting for a decision:

```bash
curl -H "X-API-Key: $K" 'http://localhost:8000/api/users?status=pending'
```

Take the bot offline for maintenance, then bring it back:

```bash
curl -X PATCH -H "X-API-Key: $K" -H 'Content-Type: application/json' \
  -d '{"enabled": false}' http://localhost:8000/api/bot/settings
```

Blocking someone does **not** delete them: their row and full message history stay, and
`DELETE /api/access/grants/{id}` puts them back to `pending`.
