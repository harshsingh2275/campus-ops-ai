/**
 * app/api/auth/login/route.ts
 *
 * Server-side Route Handler for POST /api/auth/login.
 *
 * Flow:
 *  1. Receives credentials from the browser form.
 *  2. Forwards them to the FastAPI backend.
 *  3. On success, writes the JWT into an HTTP-only, Secure, SameSite=Lax
 *     cookie — the browser JS layer never sees the raw token.
 *  4. Returns the public user object to the client.
 */

import { NextRequest, NextResponse } from "next/server";
import { apiLogin } from "@/lib/auth";

const IS_PROD = process.env.NODE_ENV === "production";

export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json();

    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password are required." },
        { status: 400 }
      );
    }

    const data = await apiLogin(email, password);

    const response = NextResponse.json(
      { user: data.user },
      { status: 200 }
    );

    // ── Set HTTP-only cookie ────────────────────────────────────────────────
    // httpOnly  → inaccessible to document.cookie / JS — XSS-safe
    // secure    → HTTPS-only in production
    // sameSite  → "lax" protects against CSRF for top-level navigations
    // path      → available to all routes
    // maxAge    → mirrors the JWT expiry so they expire together
    response.cookies.set("auth_token", data.access_token, {
      httpOnly: true,
      secure: IS_PROD,
      sameSite: "lax",
      path: "/",
      maxAge: data.expires_in, // seconds
    });

    return response;
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Login failed.";
    const status = message.includes("Invalid") ? 401 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
