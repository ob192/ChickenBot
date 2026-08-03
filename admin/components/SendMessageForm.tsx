"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { callApi } from "@/lib/client";

export default function SendMessageForm({ chatId }: { chatId: number }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [text, setText] = useState("");
  const [force, setForce] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!text.trim()) return;
    setSending(true);
    setError(null);
    try {
      await callApi("/messages/send", {
        method: "POST",
        body: JSON.stringify({ chat_id: chatId, text, force }),
      });
      setText("");
      startTransition(() => router.refresh());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={submit} style={{ marginTop: 12 }}>
      <div className="row">
        <input
          style={{ flex: 1, minWidth: 220 }}
          placeholder="Reply as the bot…"
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <button className="primary" disabled={sending || pending || !text.trim()}>
          Send
        </button>
      </div>
      <label className="row muted" style={{ fontSize: 13, marginTop: 8, gap: 6 }}>
        <input
          type="checkbox"
          checked={force}
          onChange={(event) => setForce(event.target.checked)}
        />
        Send even if the access policy excludes this user
      </label>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
