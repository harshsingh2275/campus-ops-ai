"use client";

import React from "react";
import { 
  Bot, 
  Layers, 
  Activity, 
  Send, 
  ExternalLink, 
  CheckCircle2, 
  AlertCircle,
  Sparkles,
  Database
} from "lucide-react";
import { HealthResponse } from "@/lib/api";

interface NavbarProps {
  activeTab: "portal" | "dashboard";
  setActiveTab: (tab: "portal" | "dashboard") => void;
  health: HealthResponse | null;
  healthError: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  health,
  healthError,
}) => {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 glass-panel backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / Title */}
          <div className="flex items-center space-x-3">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-[1px] shadow-glow-brand">
              <div className="w-full h-full bg-surface-50 rounded-xl flex items-center justify-center">
                <Bot className="w-5 h-5 text-indigo-400" />
              </div>
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
              </span>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="font-bold text-lg tracking-tight text-white flex items-center gap-1.5">
                  Campus Ops <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">AI</span>
                </h1>
                <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                  v1.0
                </span>
              </div>
              <p className="text-xs text-gray-400 hidden sm:block">
                Automated Ingestion & Notion Sync Engine
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center bg-surface-50/80 p-1 rounded-xl border border-white/10 shadow-inner">
            <button
              onClick={() => setActiveTab("portal")}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeTab === "portal"
                  ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-md shadow-indigo-600/30"
                  : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
              }`}
            >
              <Send className="w-4 h-4" />
              <span>Student Portal</span>
            </button>

            <button
              onClick={() => setActiveTab("dashboard")}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeTab === "dashboard"
                  ? "bg-gradient-to-r from-indigo-600 to-indigo-500 text-white shadow-md shadow-indigo-600/30"
                  : "text-gray-400 hover:text-gray-200 hover:bg-white/5"
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>Operations & Audit</span>
            </button>
          </div>

          {/* Right Status / Links */}
          <div className="flex items-center space-x-3">
            {/* Backend Health Badge */}
            <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-surface-100 border border-white/10 text-xs">
              <div className="flex items-center space-x-1.5">
                {!healthError && health ? (
                  <>
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="text-emerald-400 font-medium">Backend Live: 8000</span>
                  </>
                ) : (
                  <>
                    <span className="w-2 h-2 rounded-full bg-rose-400" />
                    <span className="text-rose-400 font-medium">Backend Offline</span>
                  </>
                )}
              </div>

              {health?.notion && (
                <>
                  <span className="text-gray-600">|</span>
                  <div className="flex items-center space-x-1 text-gray-300">
                    <Database className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="text-gray-400">
                      Notion: <span className={health.notion.configured ? "text-emerald-400 font-medium" : "text-amber-400 font-medium"}>
                        {health.notion.configured ? "Live" : "Simulation"}
                      </span>
                    </span>
                  </div>
                </>
              )}
            </div>

            {/* Swagger Docs Link */}
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs text-gray-300 transition-colors border border-white/10"
              title="Open FastAPI Swagger Docs"
            >
              <span>API Docs</span>
              <ExternalLink className="w-3 h-3 text-gray-400" />
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};
