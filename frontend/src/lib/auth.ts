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
  is_active: boolean;
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
  detail: string;
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
    throw new Error(err.detail ?? "Login failed.");
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
    throw new Error(err.detail ?? "Registration failed.");
  }

  return res.json() as Promise<RegisterResponse>;
}
