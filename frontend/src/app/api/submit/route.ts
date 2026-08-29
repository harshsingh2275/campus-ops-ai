/**
 * app/api/submit/route.ts — Server-side proxy for POST /api/submit
 *
 * Why a proxy?
 * The JWT lives in an HTTP-only cookie, so browser JS cannot read it.
 * This Route Handler runs on the server, reads the cookie, and forwards
 * the request to FastAPI with the correct Authorization header.
 *
 * Flow:
 *   Browser (no token access)
 *     → POST /api/submit  (Next.js Route Handler, server)
 *       → reads cookies().get("auth_token")
 *       → forwards body + Authorization: Bearer <token>
 *         → FastAPI POST /api/submit
 *       ← proxies response back to browser
 */

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(req: NextRequest) {
  // ── Read the HTTP-only cookie (server-only) ──────────────────────────────
  const cookieStore = cookies();
  const token = cookieStore.get("auth_token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Not authenticated. Please log in first.", code: "UNAUTHENTICATED" },
      { status: 401 }
    );
  }

  // ── Forward the request body ─────────────────────────────────────────────
  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  // ── Call the protected FastAPI endpoint ──────────────────────────────────
  try {
    const upstream = await fetch(`${API_URL}/api/submit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    const data = await upstream.json().catch(() => ({}));

    // Surface session-expiry as a recognisable code so the frontend can
    // redirect to /login rather than showing a generic error.
    if (upstream.status === 401) {
      return NextResponse.json(
        { error: data.detail ?? "Session expired. Please log in again.", code: "SESSION_EXPIRED" },
        { status: 401 }
      );
    }

    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: "Could not reach the backend. Is the server running?" },
      { status: 502 }
    );
  }
}
