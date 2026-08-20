"use client";

import React, { useState, useEffect } from "react";
import { Navbar } from "@/components/Navbar";
import { StudentPortal } from "@/components/StudentPortal";
import { OperationsDashboard } from "@/components/OperationsDashboard";
import { fetchHealth, HealthResponse } from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"portal" | "dashboard">("portal");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);

  const checkBackendHealth = async () => {
    try {
      const data = await fetchHealth();
      setHealth(data);
      setHealthError(false);
    } catch (err) {
      setHealthError(true);
    }
  };

  useEffect(() => {
    checkBackendHealth();
    const interval = setInterval(checkBackendHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#080b11] text-gray-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        healthError={healthError}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "portal" ? (
          <StudentPortal onSuccessNavigate={() => setActiveTab("dashboard")} />
        ) : (
          <OperationsDashboard health={health} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-6 text-center text-xs text-gray-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Campus Ops AI Engine — Official Notion Client & FastAPI Integration</span>
          <span>Next.js 14 App Router + Tailwind CSS</span>
        </div>
      </footer>
    </div>
  );
}
