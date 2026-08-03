"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { callApi } from "@/lib/client";
import type { AccessStatus, User } from "@/lib/types";

export default function AccessButtons({
  telegramId,
  status,
}: {
  telegramId: number;
  status: AccessStatus;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function setStatus(next: AccessStatus) {
    setSaving(true);
    setError(null);
    try {
      await callApi<User>(`/users/${telegramId}/access`, {
        method: "PATCH",
        body: JSON.stringify({ status: next }),
      });
      startTransition(() => router.refresh());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  const busy = saving || pending;
  const options: AccessStatus[] = ["allowed", "pending", "blocked"];

  return (
    <div className="row" style={{ gap: 6 }}>
      {options.map((option) => (
        <button
          key={option}
          disabled={busy || option === status}
          className={option === status ? "active" : option === "blocked" ? "danger" : ""}
          onClick={() => setStatus(option)}
        >
          {option === "allowed" ? "Allow" : option === "blocked" ? "Block" : "Reset"}
        </button>
      ))}
      {error && <span className="error">{error}</span>}
    </div>
  );
}
