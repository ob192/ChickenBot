import Link from "next/link";

import AccessButtons from "@/components/AccessButtons";
import ApiErrorBanner from "@/components/ApiErrorBanner";
import SendMessageForm from "@/components/SendMessageForm";
import { apiFetch } from "@/lib/api";
import { displayName, formatTime } from "@/lib/format";
import type { MessagePage, User } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function UserDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let user: User;
  let thread: MessagePage;
  try {
    [user, thread] = await Promise.all([
      apiFetch<User>(`/users/${id}`),
      apiFetch<MessagePage>(`/users/${id}/messages?limit=100`),
    ]);
  } catch (error) {
    return <ApiErrorBanner error={error} />;
  }

  // The API returns newest first; render oldest first like a chat.
  const messages = [...thread.items].reverse();

  return (
    <>
      <Link className="muted" href="/users">
        ← all users
      </Link>
      <h1 style={{ marginTop: 12 }}>{displayName(user)}</h1>
      <p className="subtitle mono">
        {user.telegram_id} · first seen {formatTime(user.first_seen_at)} · last seen{" "}
        {formatTime(user.last_seen_at)}
      </p>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="row spread">
          <div>
            <span className={`pill ${user.access_status}`}>{user.access_status}</span>
            {user.access_note && (
              <span className="muted" style={{ marginLeft: 8 }}>
                {user.access_note}
              </span>
            )}
          </div>
          <AccessButtons telegramId={user.telegram_id} status={user.access_status} />
        </div>
      </div>

      <div className="card">
        <h2>Conversation</h2>
        {messages.length === 0 ? (
          <p className="muted">No messages logged for this chat yet.</p>
        ) : (
          <div className="thread">
            {messages.map((message) => (
              <div key={message.id} className={`bubble ${message.direction}`}>
                {message.text ?? <span className="muted">[{message.event_type}]</span>}
                <time>
                  {formatTime(message.created_at)} · {message.event_type}
                </time>
              </div>
            ))}
          </div>
        )}
        <SendMessageForm chatId={user.telegram_id} />
      </div>
    </>
  );
}
