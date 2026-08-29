/**
 * app/api/admin/requests/[pageId]/approve/route.ts — Server-side proxy for POST /admin/requests/{pageId}/approve
 */

import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function POST(
  req: NextRequest,
  { params }: { params: { pageId: string } }
) {
  const cookieStore = cookies();
  const token = cookieStore.get("auth_token")?.value;

  if (!token) {
    return NextResponse.json(
      { error: "Not authenticated. Please log in first.", code: "UNAUTHENTICATED" },
      { status: 401 }
    );
  }

  const { pageId } = params;

  try {
    const upstream = await fetch(`${API_URL}/admin/requests/${pageId}/approve`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await upstream.json().catch(() => ({}));

    if (upstream.status === 403) {
      return NextResponse.json(
        { error: "Admin access required.", code: "FORBIDDEN" },
        { status: 403 }
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
