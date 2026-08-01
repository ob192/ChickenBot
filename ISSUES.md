# Known issues & open work

## Blockers

- [ ] **`TELEGRAM_BOT_TOKEN` is empty** in `.env` / `.env.local`. The bot connects to
      Postgres but exits at token validation until a real token from
      [@BotFather](https://t.me/BotFather) is filled in.

## Security

- [ ] **Rotate the Neon password.** The `DATABASE_URL` credential was shared in plain text
      during development (chat/terminal); rotate it in the Neon console and update
      `.env` / `.env.local`.
- [ ] **Docker Hub repo visibility.** `sasha192bunin/chickenbot` was auto-created by the
      first push and defaults to public. The image contains no secrets, but make it
      private if the bot logic itself shouldn't be public.

## Functionality

- [ ] **Game not implemented.** `chiken/` contains Easy/Medium/Hard mode images
      (6 easy, 6 medium, 5 hard + variants) but no code references them. The actual game
      flow (mode selection, image sending, answers/scoring) still needs to be designed and
      built.
- [ ] **Only `/start` is handled.** Any other message gets no reply (though it is stored).
      At minimum a fallback/help handler would improve UX.

## Infrastructure

- [ ] **No tests.** Middleware logic was verified with ad-hoc scripts during development;
      there is no committed test suite or CI.
- [ ] **No migrations** — see [CONCESSIONS.md](CONCESSIONS.md); becomes a real issue on the
      first schema change to an existing table.
- [ ] **Docker Hub image lags the repo** whenever `make deploy` isn't run after changes.
      The published image predates the conversation-logging feature until the next deploy.
- [ ] **No log retention policy** for the `messages` table (grows unboundedly).
