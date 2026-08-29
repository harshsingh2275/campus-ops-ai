/**
 * app/api/auth/register/route.ts
 *
 * Server-side Route Handler for POST /api/auth/register.
 *
 * Proxies the registration payload to the FastAPI backend and returns the
 * created user object. Does NOT set a cookie — users are redirected to
 * /login after successful registration.
 */

import { NextRequest, NextResponse } from "next/server";
import { apiRegister } from "@/lib/auth";

export async function POST(req: NextRequest) {
  try {
    const { email, name, password } = await req.json();

    if (!email || !name || !password) {
      return NextResponse.json(
        { error: "Email, name, and password are required." },
        { status: 400 }
      );
    }

    const data = await apiRegister(email, name, password);
    return NextResponse.json({ user: data.user, message: data.message }, { status: 201 });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Registration failed.";
    const status = message.includes("already exists") ? 409 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
