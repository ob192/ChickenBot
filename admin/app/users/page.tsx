import Link from "next/link";
import { Suspense } from "react";

import AccessButtons from "@/components/AccessButtons";
import ApiErrorBanner from "@/components/ApiErrorBanner";
import GrantForm from "@/components/GrantForm";
import UserFilters from "@/components/UserFilters";
import { apiFetch } from "@/lib/api";
import { displayName, formatTime } from "@/lib/format";
import type { UserPage } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function UsersPage({
  searchParams,
}: {
  searchParams: Promise<{ query?: string; status?: string }>;
}) {
  const { query, status } = await searchParams;
  const search = new URLSearchParams({ limit: "100" });
  if (query) search.set("query", query);
  if (status) search.set("status", status);

  let page: UserPage;
  try {
    page = await apiFetch<UserPage>(`/users?${search}`);
  } catch (error) {
    return <ApiErrorBanner error={error} />;
  }

  return (
    <>
      <h1>Users</h1>
      <p className="subtitle">
        {page.total} user{page.total === 1 ? "" : "s"} known to the bot. Access changes
        take effect within a few seconds.
      </p>

      <Suspense>
        <UserFilters />
      </Suspense>

      <div className="card" style={{ padding: 0, marginBottom: 16 }}>
        {page.items.length === 0 ? (
          <p className="muted" style={{ padding: 16 }}>
            No users match.
          </p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Telegram id</th>
                <th>Last seen</th>
                <th>Access</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {page.items.map((user) => (
                <tr key={user.telegram_id}>
                  <td>
                    <Link href={`/users/${user.telegram_id}`}>{displayName(user)}</Link>
                    {user.access_note && (
                      <div className="stat-label">{user.access_note}</div>
                    )}
                  </td>
                  <td className="mono">{user.telegram_id}</td>
                  <td className="muted" style={{ whiteSpace: "nowrap" }}>
                    {formatTime(user.last_seen_at)}
                  </td>
                  <td>
                    <span className={`pill ${user.access_status}`}>
                      {user.access_status}
                    </span>
                  </td>
                  <td>
                    <AccessButtons
                      telegramId={user.telegram_id}
                      status={user.access_status}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <GrantForm />
    </>
  );
}
