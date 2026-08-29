"use client";

/**
 * app/(auth)/login/page.tsx — Login Page
 */

import { useState, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, LogIn, Loader2, ShieldCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { loginUser } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const emailRef = useRef<HTMLInputElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error ?? "Login failed. Please try again.");
        return;
      }

      if (data.user) {
        loginUser(data.user);
      }

      setSuccess(true);
      
      // Role-based redirect: admin -> /operations, student -> /student-portal
      const targetPath = data.user?.role === "admin" ? "/operations" : "/student-portal";
      setTimeout(() => router.push(targetPath), 800);
    } catch {
      setError("Network error. Make sure the backend is running.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <>
      {/* ── Brand mark ────────────────────────────────────────────────── */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-glow-brand">
          <ShieldCheck className="h-7 w-7 text-white" strokeWidth={1.8} />
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Welcome back
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            Sign in to your CampusOps AI account
          </p>
        </div>
      </div>

      {/* ── Card ──────────────────────────────────────────────────────── */}
      <div className="glass-panel-elevated rounded-2xl p-8">
        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          {/* Error banner */}
          {error && (
            <div
              role="alert"
              className="flex items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300 animate-fadeIn"
            >
              <span className="mt-0.5 shrink-0 text-rose-400">✕</span>
              {error}
            </div>
          )}

          {/* Success banner */}
          {success && (
            <div
              role="status"
              className="flex items-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300 animate-fadeIn"
            >
              <span className="shrink-0">✓</span>
              Signed in! Redirecting…
            </div>
          )}

          {/* Email */}
          <div className="space-y-1.5">
            <label
              htmlFor="login-email"
              className="block text-xs font-medium uppercase tracking-widest text-gray-400"
            >
              Email address
            </label>
            <input
              id="login-email"
              ref={emailRef}
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="glass-input w-full rounded-xl px-4 py-3 text-sm placeholder:text-gray-600 focus:ring-0"
            />
          </div>

          {/* Password */}
          <div className="space-y-1.5">
            <label
              htmlFor="login-password"
              className="block text-xs font-medium uppercase tracking-widest text-gray-400"
            >
              Password
            </label>
            <div className="relative">
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="glass-input w-full rounded-xl px-4 py-3 pr-11 text-sm placeholder:text-gray-600 focus:ring-0"
              />
              <button
                type="button"
                aria-label={showPassword ? "Hide password" : "Show password"}
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            id="login-submit"
            type="submit"
            disabled={isLoading || success}
            className="group relative mt-2 flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-glow-brand transition-all duration-200 hover:from-indigo-500 hover:to-violet-500 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
          >
            {/* shimmer sweep on hover */}
            <span
              aria-hidden="true"
              className="absolute inset-0 -skew-x-12 translate-x-[-150%] bg-white/10 transition-transform duration-700 group-hover:translate-x-[150%]"
            />
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <LogIn className="h-4 w-4" />
            )}
            {isLoading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {/* Divider */}
        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-xs text-gray-600">New here?</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>

        <Link
          href="/register"
          className="flex w-full items-center justify-center rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-gray-300 transition-all hover:border-indigo-500/40 hover:bg-indigo-500/10 hover:text-white"
        >
          Create an account
        </Link>
      </div>

      <p className="mt-6 text-center text-xs text-gray-600">
        Your credentials are encrypted in transit and your password is hashed
        with Argon2id.
      </p>
    </>
  );
}
