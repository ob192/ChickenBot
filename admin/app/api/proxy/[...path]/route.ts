import { NextRequest, NextResponse } from "next/server";

import { API_BASE_URL, apiHeaders } from "@/lib/api";

/**
 * Forwards browser calls to the FastAPI service, injecting the API key on the
 * server so it is never shipped to the client.
 *
 * /api/proxy/bot/settings  ->  <API_BASE_URL>/api/bot/settings
 */
async function forward(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const search = request.nextUrl.search;
  const url = `${API_BASE_URL}/api/${path.join("/")}${search}`;

  const body =
    request.method === "GET" || request.method === "DELETE"
      ? undefined
      : await request.text();

  try {
    const upstream = await fetch(url, {
      method: request.method,
      headers: apiHeaders({ "Content-Type": "application/json" }),
      body,
      cache: "no-store",
    });
    const text = await upstream.text();
    return new NextResponse(text || null, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    return NextResponse.json(
      { detail: `API unreachable at ${API_BASE_URL}: ${String(error)}` },
      { status: 502 },
    );
  }
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const PUT = forward;
export const DELETE = forward;
