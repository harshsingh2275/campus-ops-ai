"use client";

/**
 * app/(auth)/register/page.tsx — Registration Page
 */

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Eye,
  EyeOff,
  UserPlus,
  Loader2,
  ShieldCheck,
  CheckCircle2,
} from "lucide-react";

// ── Password strength helper ──────────────────────────────────────────────────

function getPasswordStrength(pw: string): {
  score: number; // 0-4
  label: string;
  color: string;
} {
  if (!pw) return { score: 0, label: "", color: "" };
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw) && /[^A-Za-z0-9]/.test(pw)) score++;

  const labels = ["Weak", "Fair", "Good", "Strong"];
  const colors = [
    "bg-rose-500",
    "bg-amber-500",
    "bg-emerald-400",
    "bg-emerald-500",
  ];
  return { score, label: labels[score - 1] ?? "", color: colors[score - 1] ?? "" };
}

export default function RegisterPage() {
  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const strength = getPasswordStrength(password);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setIsLoading(true);

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.error ?? "Registration failed. Please try again.");
        return;
      }

      setSuccess(true);
      setTimeout(() => router.push("/login"), 1500);
    } catch {
      setError("Network error. Make sure the backend is running.");
    } finally {
      setIsLoading(false);
    }
  }

  // ── Success state ─────────────────────────────────────────────────────────
  if (success) {
    return (
      <div className="glass-panel-elevated flex flex-col items-center gap-4 rounded-2xl p-10 text-center animate-scaleUp">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20">
          <CheckCircle2 className="h-8 w-8 text-emerald-400" />
        </div>
        <h2 className="text-xl font-bold text-white">Account created!</h2>
        <p className="text-sm text-gray-400">
          Redirecting you to sign in…
        </p>
        <div className="h-1 w-32 overflow-hidden rounded-full bg-white/10">
          <div className="h-full w-full animate-shimmer rounded-full bg-gradient-to-r from-transparent via-emerald-400 to-transparent bg-[length:200%_100%]" />
        </div>
      </div>
    );
  }

  return (
    <>
      {/* ── Brand mark ────────────────────────────────────────────────── */}
      <div className="mb-8 flex flex-col items-center gap-3">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 shadow-glow-brand">
          <ShieldCheck className="h-7 w-7 text-white" strokeWidth={1.8} />
        </div>
        <div className="text-center">
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Create your account
          </h1>
          <p className="mt-1 text-sm text-gray-400">
            Join CampusOps AI — it&apos;s free
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

          {/* Full name */}
          <div className="space-y-1.5">
            <label
              htmlFor="register-name"
              className="block text-xs font-medium uppercase tracking-widest text-gray-400"
            >
              Full name
            </label>
            <input
              id="register-name"
              type="text"
              autoComplete="name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Alex Johnson"
              className="glass-input w-full rounded-xl px-4 py-3 text-sm placeholder:text-gray-600 focus:ring-0"
            />
          </div>

          {/* Email */}
          <div className="space-y-1.5">
            <label
              htmlFor="register-email"
              className="block text-xs font-medium uppercase tracking-widest text-gray-400"
            >
              Email address
            </label>
            <input
              id="register-email"
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
              htmlFor="register-password"
              className="block text-xs font-medium uppercase tracking-widest text-gray-400"
            >
              Password
            </label>
            <div className="relative">
              <input
                id="register-password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Min. 8 characters"
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

            {/* Password strength meter */}
            {password.length > 0 && (
              <div className="space-y-1.5 animate-fadeIn">
                <div className="flex gap-1">
                  {[1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                        i <= strength.score
                          ? strength.color
                          : "bg-white/10"
                      }`}
                    />
                  ))}
                </div>
                {strength.label && (
                  <p className="text-xs text-gray-500">
                    Strength:{" "}
                    <span
                      className={
                        strength.score <= 1
                          ? "text-rose-400"
                          : strength.score === 2
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }
                    >
                      {strength.label}
                    </span>
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Submit */}
          <button
            id="register-submit"
            type="submit"
            disabled={isLoading}
            className="group relative mt-2 flex w-full items-center justify-center gap-2 overflow-hidden rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-glow-brand transition-all duration-200 hover:from-violet-500 hover:to-indigo-500 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span
              aria-hidden="true"
              className="absolute inset-0 -skew-x-12 translate-x-[-150%] bg-white/10 transition-transform duration-700 group-hover:translate-x-[150%]"
            />
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <UserPlus className="h-4 w-4" />
            )}
            {isLoading ? "Creating account…" : "Create account"}
          </button>
        </form>

        {/* Divider */}
        <div className="my-6 flex items-center gap-3">
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-xs text-gray-600">Already have an account?</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>

        <Link
          href="/login"
          className="flex w-full items-center justify-center rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-gray-300 transition-all hover:border-indigo-500/40 hover:bg-indigo-500/10 hover:text-white"
        >
          Sign in instead
        </Link>
      </div>

      <p className="mt-6 text-center text-xs text-gray-600">
        By creating an account you agree to our Terms of Service.
      </p>
    </>
  );
}
