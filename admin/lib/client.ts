"use client";

/** Browser-side calls go through the Next.js proxy, which adds the API key. */
export async function callApi<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api/proxy${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init.headers },
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new Error(data?.detail ?? `Request failed (${response.status})`);
  }
  return data as T;
}
