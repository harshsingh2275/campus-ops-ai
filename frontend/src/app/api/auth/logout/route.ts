/**
 * app/api/auth/logout/route.ts
 *
 * Clears the auth_token cookie by overwriting it with an immediately-expired
 * value.  Safe to call even if no cookie exists.
 */

import { NextResponse } from "next/server";

export async function POST() {
  const response = NextResponse.json({ message: "Logged out." }, { status: 200 });

  response.cookies.set("auth_token", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: 0, // immediately expired
  });

  return response;
}
