import Link from "next/link";

import ApiErrorBanner from "@/components/ApiErrorBanner";
import { apiFetch } from "@/lib/api";
import { formatTime } from "@/lib/format";
import type { MessagePage } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function MessagesPage({
  searchParams,
}: {
  searchParams: Promise<{ offset?: string }>;
}) {
  const { offset: rawOffset } = await searchParams;
  const offset = Number(rawOffset ?? 0) || 0;
  const limit = 100;

  let page: MessagePage;
  try {
    page = await apiFetch<MessagePage>(`/messages?limit=${limit}&offset=${offset}`);
  } catch (error) {
    return <ApiErrorBanner error={error} />;
  }

  return (
    <>
      <h1>Message log</h1>
      <p className="subtitle">
        Everything the bot received and sent, newest first — including updates that no
        handler answered.
      </p>

      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead>
            <tr>
              <th>When</th>
              <th>Dir</th>
              <th>Chat</th>
              <th>Event</th>
              <th>Text</th>
            </tr>
          </thead>
          <tbody>
            {page.items.map((message) => (
              <tr key={message.id}>
                <td className="muted" style={{ whiteSpace: "nowrap" }}>
                  {formatTime(message.created_at)}
                </td>
                <td>
                  <span className="pill">{message.direction}</span>
                </td>
                <td className="mono">
                  {message.chat_id ? (
                    <Link href={`/users/${message.chat_id}`}>{message.chat_id}</Link>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="muted">{message.event_type}</td>
                <td>{message.text ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="row" style={{ marginTop: 16, gap: 12 }}>
        {offset > 0 && (
          <Link className="button" href={`/messages?offset=${Math.max(0, offset - limit)}`}>
            ← newer
          </Link>
        )}
        {page.items.length === limit && (
          <Link className="button" href={`/messages?offset=${offset + limit}`}>
            older →
          </Link>
        )}
      </div>
    </>
  );
}
