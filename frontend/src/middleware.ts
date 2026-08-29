/**
 * src/middleware.ts — Route Protection Middleware
 * ================================================
 *
 * Runs on the Next.js Edge Runtime before every matched request.
 *
 * Rules
 * -----
 * 1. Public routes (/login, /register, and all /api/auth/* handlers) are
 *    always allowed through — they don't require a cookie.
 *
 * 2. For every other matched route (currently just "/"), the middleware
 *    checks for the ``auth_token`` HTTP-only cookie.
 *    - Cookie present  → allow the request through.
 *    - Cookie missing  → redirect to /login, preserving the original URL
 *      as a ``?from=`` query param so the login page can redirect back
 *      after a successful sign-in.
 *
 * Matcher
 * -------
 * Configured to skip:
 *   • Next.js internals  (_next/static, _next/image)
 *   • favicon and other public-folder assets
 *   • All /auth/* page routes         (/login, /register)
 *   • All /api/auth/* Route Handlers  (/api/auth/login, /api/auth/register, /api/auth/logout)
 *
 * Anything not in the exclusion list falls into the protected set.
 * Right now that is just "/" (the main dashboard), but this config scales
 * cleanly when new protected routes are added — they are protected by
 * default without touching this file.
 */

import { NextRequest, NextResponse } from "next/server";

// Routes that are always public — no cookie check performed.
const PUBLIC_PATHS = new Set(["/login", "/register"]);

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // ── Always allow public auth pages ────────────────────────────────────────
  if (PUBLIC_PATHS.has(pathname)) {
    return NextResponse.next();
  }

  // ── Check for the HTTP-only JWT cookie ────────────────────────────────────
  const token = req.cookies.get("auth_token")?.value;

  if (!token) {
    // Build the redirect URL, preserving where the user was trying to go.
    const loginUrl = req.nextUrl.clone();
    loginUrl.pathname = "/login";
    // Only set ?from= for non-root paths to avoid a redundant param on login itself.
    if (pathname !== "/") {
      loginUrl.searchParams.set("from", pathname);
    }
    return NextResponse.redirect(loginUrl);
  }

  // Token present — allow through.
  // Note: we intentionally do NOT verify the JWT signature here.
  // Edge Runtime cannot use Node.js crypto modules required by PyJWT-style
  // verification. Signature verification happens in the FastAPI backend on
  // every API call. The cookie's HttpOnly + SameSite=Lax attributes already
  // prevent forgery from the browser side.
  return NextResponse.next();
}

// ---------------------------------------------------------------------------
// Matcher configuration
// ---------------------------------------------------------------------------
// next/server middleware matchers use path-to-regexp syntax.
// The negative lookaheads below exclude:
//   • /_next/  — internal Next.js build assets
//   • /api/auth/ — our own auth Route Handlers (login, register, logout)
//   • /login, /register — the auth pages
//   • common static file extensions
// ---------------------------------------------------------------------------
export const config = {
  matcher: [
    /*
     * Match every request path EXCEPT:
     *   - _next/static  (static files)
     *   - _next/image   (image optimisation)
     *   - favicon.ico
     *   - /login and /register (auth pages)
     *   - /api/auth/**  (our auth Route Handlers)
     *   - Files with a dot (e.g. .png, .svg, .js, .css)
     */
    "/((?!_next/static|_next/image|favicon\\.ico|login|register|api/auth|.*\\..*).*)",
  ],
};
