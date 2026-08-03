"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import type { AccessStatus } from "@/lib/types";

const STATUSES: (AccessStatus | "")[] = ["", "pending", "allowed", "blocked"];

export default function UserFilters() {
  const router = useRouter();
  const params = useSearchParams();
  const [query, setQuery] = useState(params.get("query") ?? "");
  const status = params.get("status") ?? "";

  function navigate(next: { query?: string; status?: string }) {
    const search = new URLSearchParams();
    const q = next.query ?? query;
    const s = next.status ?? status;
    if (q) search.set("query", q);
    if (s) search.set("status", s);
    router.push(`/users${search.toString() ? `?${search}` : ""}`);
  }

  return (
    <div className="row spread" style={{ marginBottom: 16 }}>
      <form
        className="row"
        onSubmit={(event) => {
          event.preventDefault();
          navigate({});
        }}
      >
        <input
          placeholder="Search id, username or name"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          style={{ width: 240 }}
        />
        <button>Search</button>
      </form>
      <div className="row" style={{ gap: 6 }}>
        {STATUSES.map((value) => (
          <button
            key={value || "all"}
            className={status === value ? "active" : ""}
            onClick={() => navigate({ status: value })}
          >
            {value || "all"}
          </button>
        ))}
      </div>
    </div>
  );
}
