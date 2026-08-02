import "server-only";

/**
 * Server-side FastAPI client. The API key lives in the Next.js server process
 * only — the browser talks to /api/proxy/* instead and never sees it.
 */
export const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";
const API_KEY = process.env.API_KEY ?? "";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export function apiHeaders(extra: HeadersInit = {}): HeadersInit {
  return { "X-API-Key": API_KEY, ...extra };
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}/api${path}`, {
    ...init,
    headers: apiHeaders(init.headers),
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text();
    let detail = body;
    try {
      detail = JSON.parse(body).detail ?? body;
    } catch {
      /* plain-text error body */
    }
    throw new ApiError(response.status, detail || response.statusText);
  }

  return (await response.json()) as T;
}
