import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

export const metadata: Metadata = {
  title: "CampusOps AI — Intelligent Campus Operations & Notion Automation",
  description:
    "An end-to-end AI-powered campus operations platform that parses unstructured student requests, syncs structured data to Notion databases, and auto-executes approved tickets with a background engine. Built for the Notion Track hackathon.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#080b11] text-gray-100 min-h-screen antialiased selection:bg-indigo-500 selection:text-white">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
