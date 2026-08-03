# Known issues & open work

## Blockers

None. All three services are configured and have been run successfully against the live
Neon database — the bot connects as
[@chicken_hack_daniel_bot](https://t.me/chicken_hack_daniel_bot). Nothing is deployed or
running permanently: start them with `make bot` / `make api` / `make admin`, or the whole
stack with `make dev` (see [docs/deployment.md](docs/deployment.md)).

## Security

- [ ] **Rotate the Neon password.** The `DATABASE_URL` credential was shared in plain text
      during development (chat/terminal); rotate it in the Neon console and update
      `.env` / `.env.local`.
- [ ] **Rotate the bot token if it leaves this machine.** `TELEGRAM_BOT_TOKEN` was also
      pasted in plain text during development; `/revoke` in
      [@BotFather](https://t.me/BotFather) issues a new one.
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
