"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { callApi } from "@/lib/client";
import type { AccessStatus, User } from "@/lib/types";

/** Allow (or block) a Telegram id that has never written to the bot. */
export default function GrantForm() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [telegramId, setTelegramId] = useState("");
  const [note, setNote] = useState("");
  const [status, setStatus] = useState<AccessStatus>("allowed");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const id = Number(telegramId.trim());
    if (!Number.isInteger(id) || id === 0) {
      setError("Enter a numeric Telegram id");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await callApi<User>("/access/grants", {
        method: "POST",
        body: JSON.stringify({ telegram_id: id, status, note: note || null }),
      });
      setTelegramId("");
      setNote("");
      startTransition(() => router.refresh());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h2>Pre-authorize an id</h2>
      <div className="row">
        <input
          placeholder="Telegram id"
          value={telegramId}
          onChange={(event) => setTelegramId(event.target.value)}
          style={{ width: 150 }}
        />
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value as AccessStatus)}
        >
          <option value="allowed">allowed</option>
          <option value="blocked">blocked</option>
        </select>
        <input
          placeholder="Note (optional)"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          style={{ flex: 1, minWidth: 160 }}
        />
        <button className="primary" disabled={saving || pending}>
          Add
        </button>
      </div>
      <p className="stat-label" style={{ marginTop: 8, marginBottom: 0 }}>
        The profile fills itself in the first time that person messages the bot.
      </p>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
