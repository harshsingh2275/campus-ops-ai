/**
 * lib/auth.ts — Typed client for the FastAPI auth API
 *
 * These functions are called from Next.js Route Handlers (server-side) and
 * never run in the browser directly, so API_URL can safely reference the
 * internal backend URL.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// ─── Shapes that mirror the FastAPI response schemas ──────────────────────────

export interface UserPublic {
  id: number;
  email: string;
  name: string;
  role: "admin" | "student" | string;
  is_active: boolean;
}

export function decodeJwtPayload(token: string): Record<string, any> | null {
  try {
    const parts = token.split(".");
    if (parts.length < 2) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number; // seconds
  user: UserPublic;
}

export interface RegisterResponse {
  message: string;
  user: UserPublic;
}

export interface AuthError {
  // FastAPI returns a plain string for most errors, but a Pydantic 422
  // validation error returns an array of { loc, msg, type } objects.
  detail: string | Array<{ loc: string[]; msg: string; type: string }> | unknown;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Normalise FastAPI's `detail` field into a human-readable string.
 *
 * FastAPI's `detail` can be:
 *   - A plain string  → used as-is.
 *   - A Pydantic 422 array  → each item has { loc, msg, type }; we join the
 *     `msg` values so the user sees e.g. "value is not a valid email address".
 *   - Anything else  → fall back to the provided fallback string.
 */
function normaliseDetail(
  detail: AuthError["detail"],
  fallback: string
): string {
  if (!detail) return fallback;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "object" && item !== null && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return String(item);
      })
      .filter(Boolean);
    return messages.length > 0 ? messages.join("; ") : fallback;
  }

  return fallback;
}

// ─── API helpers ──────────────────────────────────────────────────────────────

export async function apiLogin(
  email: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const err: AuthError = await res.json().catch(() => ({ detail: "Login failed." }));
    throw new Error(normaliseDetail(err.detail, "Login failed."));
  }

  return res.json() as Promise<TokenResponse>;
}

export async function apiRegister(
  email: string,
  name: string,
  password: string
): Promise<RegisterResponse> {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, name, password }),
  });

  if (!res.ok) {
    const err: AuthError = await res.json().catch(() => ({ detail: "Registration failed." }));
    throw new Error(normaliseDetail(err.detail, "Registration failed."));
  }

  return res.json() as Promise<RegisterResponse>;
}
