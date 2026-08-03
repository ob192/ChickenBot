"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { callApi } from "@/lib/client";
import type { AccessMode, BotSettings } from "@/lib/types";

export default function BotControls({ settings }: { settings: BotSettings }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState(settings.access_denied_message);

  const busy = saving || pending;

  async function patch(body: Partial<BotSettings>) {
    setSaving(true);
    setError(null);
    try {
      await callApi<BotSettings>("/bot/settings", {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      startTransition(() => router.refresh());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  const modes: { value: AccessMode; label: string; hint: string }[] = [
    { value: "open", label: "Open", hint: "everyone except blocked users" },
    { value: "allowlist", label: "Allowlist", hint: "only allowed users" },
  ];

  return (
    <div className="card">
      <h2>Bot control</h2>

      <div className="row spread" style={{ marginBottom: 16 }}>
        <div>
          <div>
            Bot is{" "}
            <strong style={{ color: settings.enabled ? "var(--ok)" : "var(--danger)" }}>
              {settings.enabled ? "answering" : "silenced"}
            </strong>
          </div>
          <div className="stat-label">
            While silenced, updates are still logged but no handler runs.
          </div>
        </div>
        <button
          className={settings.enabled ? "danger" : "primary"}
          disabled={busy}
          onClick={() => patch({ enabled: !settings.enabled })}
        >
          {settings.enabled ? "Silence bot" : "Enable bot"}
        </button>
      </div>

      <div style={{ marginBottom: 16 }}>
        <div className="stat-label" style={{ marginBottom: 6 }}>
          Access mode
        </div>
        <div className="row">
          {modes.map((mode) => (
            <button
              key={mode.value}
              className={settings.access_mode === mode.value ? "active" : ""}
              disabled={busy}
              onClick={() => patch({ access_mode: mode.value })}
              title={mode.hint}
            >
              {mode.label}
            </button>
          ))}
          <span className="muted" style={{ fontSize: 13 }}>
            {modes.find((m) => m.value === settings.access_mode)?.hint}
          </span>
        </div>
      </div>

      <div>
        <div className="stat-label" style={{ marginBottom: 6 }}>
          Access denied reply
        </div>
        <div className="row">
          <input
            style={{ flex: 1, minWidth: 220 }}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="Leave empty to stay silent"
          />
          <button
            disabled={busy || message === settings.access_denied_message}
            onClick={() => patch({ access_denied_message: message })}
          >
            Save
          </button>
        </div>
      </div>

      {error && <p className="error">{error}</p>}
    </div>
  );
}
