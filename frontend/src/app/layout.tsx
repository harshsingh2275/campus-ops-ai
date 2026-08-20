import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Campus Ops AI | Intelligent Operations & Notion Sync",
  description: "AI-Powered Campus Operations, Student Request Ingestion, Automated Notion Sync & Audit System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080b11] text-gray-100 min-h-screen antialiased selection:bg-indigo-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
