# Known issues & open work

## Blockers

- [ ] **`TELEGRAM_BOT_TOKEN` is empty** in `.env` / `.env.local`. The bot connects to
      Postgres but exits at token validation until a real token from
      [@BotFather](https://t.me/BotFather) is filled in. The API starts fine without it but
      reports `reachable: false` on `/api/bot/status` and cannot send messages.

## Security

- [ ] **Rotate the Neon password.** The `DATABASE_URL` credential was shared in plain text
      during development (chat/terminal); rotate it in the Neon console and update
      `.env` / `.env.local`.
- [ ] **The admin UI has no login.** It holds the API key server-side, so the key never
      reaches the browser, but anyone who can reach port 3000 is an admin. Keep it on
      localhost / behind a VPN until a login or authenticating proxy is added.
- [ ] **One static API key, no per-operator identity.** `access_note` records why access
      changed but not who changed it. See [CONCESSIONS.md](CONCESSIONS.md).
- [ ] **Docker Hub repo visibility.** `sasha192bunin/chickenbot` was auto-created by the
      first push and defaults to public. The images contain no secrets, but make them
      private if the bot logic itself shouldn't be public.

## Functionality

- [ ] **Game not implemented.** `chiken/` contains Easy/Medium/Hard mode images
      (6 easy, 6 medium, 5 hard + variants) but no code references them. The actual game
      flow (mode selection, image sending, answers/scoring) still needs to be designed and
      built.
- [ ] **Only `/start` is handled.** Any other message gets no reply (though it is stored).
      At minimum a fallback/help handler would improve UX.
- [ ] **API can only send plain text.** `POST /api/messages/send` wraps `sendMessage`
      only — no photos, keyboards, or broadcast-to-many.
- [ ] **No group support in the access model.** Access is per Telegram *user*; a group chat
      is allowed as soon as the sending member is. Group-level rules would need their own
      table.

## Infrastructure

- [ ] **No tests.** Bot middleware, access decisions and the API were verified end-to-end
      against a throwaway Postgres during development, but there is no committed test suite
      or CI. pytest + httpx `ASGITransport` over a test database is the obvious next step.
- [ ] **No migrations** — see [CONCESSIONS.md](CONCESSIONS.md). The access columns are added
      by an `ALTER TABLE … IF NOT EXISTS` list in `core/db.py`; the next schema change that
      is not a plain column addition needs a real tool.
- [ ] **Docker Hub images lag the repo** whenever `make deploy` isn't run after changes.
      Both `chickenbot` and `chickenbot-admin` must be pushed.
- [ ] **No log retention policy** for the `messages` table (grows unboundedly).
- [ ] **No rate limiting on the API**, and no request logging beyond uvicorn's access log.
