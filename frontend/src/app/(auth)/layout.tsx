/**
 * app/(auth)/layout.tsx
 *
 * Shared layout for /login and /register.
 * Provides the full-screen dark background with animated glow accents and
 * centers the auth card vertically and horizontally.
 */

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CampusOps AI — Sign In",
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-[#060810]">
      {/* ── Ambient glow blobs ─────────────────────────────────────────── */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0"
      >
        {/* top-left purple */}
        <div className="absolute -top-40 -left-40 h-[520px] w-[520px] rounded-full bg-indigo-600/20 blur-[120px]" />
        {/* bottom-right cyan */}
        <div className="absolute -bottom-40 -right-32 h-[480px] w-[480px] rounded-full bg-cyan-500/15 blur-[100px]" />
        {/* center subtle */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[300px] w-[600px] rounded-full bg-violet-600/10 blur-[90px]" />
      </div>

      {/* ── Subtle grid overlay ───────────────────────────────────────── */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 z-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />

      {/* ── Page content ─────────────────────────────────────────────── */}
      <div className="relative z-10 w-full max-w-md px-4 py-12 animate-fadeIn">
        {children}
      </div>
    </div>
  );
}
