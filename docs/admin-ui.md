# Admin UI

A [Next.js 15](https://nextjs.org/) (App Router, React 19, TypeScript) admin panel that
talks to the [API](api.md). It holds no database credentials and no bot token — everything
goes through FastAPI.

Run it with `make admin` → <http://localhost:3000> (the API must be running too).

## Layout

```
admin/app/page.tsx                    dashboard: status, counters, bot controls, latest activity
admin/app/users/page.tsx              user list: search, status filter, allow/block, pre-authorize
admin/app/users/[id]/page.tsx         one user: profile, access, conversation, reply box
admin/app/messages/page.tsx           the full message log with paging
admin/app/api/proxy/[...path]/route.ts server-side proxy that injects the API key
admin/components/                     client components (the interactive bits)
admin/lib/api.ts                      server-side API client
admin/lib/client.ts                   browser-side client (talks to the proxy)
```

## How data flows

- **Reads** happen in server components via `lib/api.ts`, which calls
  `${API_BASE_URL}/api/...` with the `X-API-Key` header and `cache: "no-store"`.
- **Writes** happen in client components via `lib/client.ts`, which calls
  `/api/proxy/...` on the Next.js server; the proxy route forwards to FastAPI and adds the
  key there. After a write the component calls `router.refresh()` so the server components
  re-render with fresh data.

The API key therefore lives only in the Next.js server process — it is never part of the
HTML or the client bundle.

## Pages

**Dashboard** — bot identity from `getMe`, user/message counters, and the controls:
silence/enable the bot, switch `open` ⇄ `allowlist`, edit the access-denied reply. Plus the
eight most recent log entries.

**Users** — searchable, filterable table (id, username, first/last name). Each row has
Allow / Reset / Block buttons and links to the conversation. At the bottom, a form to
pre-authorize a Telegram id that has never written in.

**User detail** — profile, access status with the same controls, the conversation rendered
as a thread (incoming left, outgoing right), and a box to reply as the bot. The "send even
if the access policy excludes this user" checkbox maps to the API's `force` flag.

**Messages** — the raw log, newest first, paged 100 at a time, with links back to the chat.

## Configuration

`admin/.env.local` (see `admin/.env.example`):

| Variable       | Description                                          |
| -------------- | ---------------------------------------------------- |
| `API_BASE_URL` | Where FastAPI lives, no trailing slash               |
| `API_KEY`      | Must match `API_KEY` in the project root `.env`      |

Both are server-side only — do **not** prefix them with `NEXT_PUBLIC_`. They are read when
a request is served, so changing them means restarting the dev server.

Port 3000 is only the default: `npm run dev -- -p 3001` moves the panel, and
`API_BASE_URL` moves the API it talks to. The proxy means the browser only ever calls the
Next.js origin, so moving either port needs no CORS change.

## Troubleshooting

- **"Cannot reach the API" banner** — every page catches API failures and renders the
  reason (connection refused, `401` on a key mismatch, …). Check the API is up
  (`curl $API_BASE_URL/health`) and that both `API_KEY` values match.
- **Empty user list** — expected until somebody messages the bot. Pre-authorize an id from
  the form at the bottom of the users page to create the first row.
- **"TELEGRAM_BOT_TOKEN is not configured"** when sending — the API started without a
  valid token. Everything else on the panel still works; see [api.md](api.md).

## Note on authentication

The panel itself has no login: anyone who can open it can use the API key it holds. Run it
on localhost or behind an authenticating proxy/VPN — see [CONCESSIONS.md](../CONCESSIONS.md).
