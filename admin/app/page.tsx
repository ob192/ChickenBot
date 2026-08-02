import Link from "next/link";

import ApiErrorBanner from "@/components/ApiErrorBanner";
import BotControls from "@/components/BotControls";
import { apiFetch } from "@/lib/api";
import { formatTime } from "@/lib/format";
import type { BotStatus, MessagePage } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let status: BotStatus;
  let recent: MessagePage;
  try {
    [status, recent] = await Promise.all([
      apiFetch<BotStatus>("/bot/status"),
      apiFetch<MessagePage>("/messages?limit=8"),
    ]);
  } catch (error) {
    return <ApiErrorBanner error={error} />;
  }

  const { identity, users, messages } = status;

  return (
    <>
      <h1>Dashboard</h1>
      <p className="subtitle">
        {identity.reachable ? (
          <>
            Connected to <span className="mono">@{identity.username}</span> (id{" "}
            {identity.id})
          </>
        ) : (
          <span style={{ color: "var(--danger)" }}>
            Telegram unreachable: {identity.error}
          </span>
        )}
      </p>

      <div className="grid">
        <div className="card">
          <div className="stat">{users.total ?? 0}</div>
          <div className="stat-label">users known</div>
        </div>
        <div className="card">
          <div className="stat" style={{ color: "var(--ok)" }}>
            {users.allowed ?? 0}
          </div>
          <div className="stat-label">allowed</div>
        </div>
        <div className="card">
          <div className="stat" style={{ color: "var(--danger)" }}>
            {users.blocked ?? 0}
          </div>
          <div className="stat-label">blocked</div>
        </div>
        <div className="card">
          <div className="stat">{messages.total ?? 0}</div>
          <div className="stat-label">
            messages logged ({messages.incoming ?? 0} in / {messages.outgoing ?? 0} out)
          </div>
        </div>
      </div>

      <BotControls settings={status.settings} />

      <div className="card" style={{ marginTop: 16 }}>
        <div className="row spread">
          <h2>Latest activity</h2>
          <Link className="muted" href="/messages">
            view all →
          </Link>
        </div>
        {recent.items.length === 0 ? (
          <p className="muted">Nothing logged yet.</p>
        ) : (
          <table>
            <tbody>
              {recent.items.map((message) => (
                <tr key={message.id}>
                  <td className="muted" style={{ whiteSpace: "nowrap" }}>
                    {formatTime(message.created_at)}
                  </td>
                  <td>
                    <span className="pill">
                      {message.direction === "in" ? "in" : "out"}
                    </span>
                  </td>
                  <td className="mono">
                    {message.chat_id ? (
                      <Link href={`/users/${message.chat_id}`}>{message.chat_id}</Link>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{message.text ?? <span className="muted">{message.event_type}</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
