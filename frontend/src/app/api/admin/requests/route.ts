/**
 * app/api/admin/requests/route.ts — Server-side proxy for GET /admin/requests
 *
 * Reads HTTP-only cookie and forwards to FastAPI GET /admin/requests with Authorization header.
 */

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET(req: NextRequest) {
  const cookieStore = cookies();
  const token = cookieStore.get("auth_token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Not authenticated. Please log in first.", code: "UNAUTHENTICATED" },
      { status: 401 }
    );
  }

  // Forward query parameters
  const { searchParams } = new URL(req.url);
  const targetUrl = new URL(`${API_URL}/admin/requests`);
  searchParams.forEach((value, key) => {
    targetUrl.searchParams.set(key, value);
  });

  try {
    const upstream = await fetch(targetUrl.toString(), {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      cache: "no-store",
    });

    const data = await upstream.json().catch(() => ({}));

    if (upstream.status === 403) {
      return NextResponse.json(
        { error: "Admin access required.", code: "FORBIDDEN" },
        { status: 403 }
      );
    }

    if (upstream.status === 401) {
      return NextResponse.json(
        { error: data.detail ?? "Session expired. Please log in again.", code: "SESSION_EXPIRED" },
        { status: 401 }
      );
    }

    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json(
      { error: "Could not reach the backend server." },
      { status: 502 }
    );
  }
}
