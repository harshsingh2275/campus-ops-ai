"use client";

import React, { useState, useEffect } from "react";
import { 
  Activity, 
  Search, 
  RefreshCw, 
  Clock, 
  ChevronDown, 
  ChevronUp, 
  Zap, 
  ShieldCheck, 
  FlaskConical,
  Wrench,
  CalendarDays,
  GraduationCap,
  Wifi,
  HelpCircle,
  Ticket,
  CheckCircle2
} from "lucide-react";
import { 
  fetchRequests, 
  SubmitResponse, 
  HealthResponse 
} from "@/lib/api";
import { formatTimeAgo } from "@/lib/utils";

interface OperationsDashboardProps {
  health?: HealthResponse | null;
}

export const OperationsDashboard: React.FC<OperationsDashboardProps> = () => {
  const [requests, setRequests] = useState<SubmitResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedPriority, setSelectedPriority] = useState("All");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedRequestId, setExpandedRequestId] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const reqData = await fetchRequests({
        category: selectedCategory !== "All" ? selectedCategory : undefined,
        priority: selectedPriority !== "All" ? selectedPriority : undefined,
        search: searchQuery || undefined,
      });
      setRequests(reqData);
    } catch (err) {
      console.error("Error fetching requests:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedCategory, selectedPriority, searchQuery]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    return () => clearInterval(interval);
  }, [autoRefresh, selectedCategory, selectedPriority, searchQuery]);

  // Compute Student Metrics
  const totalRequests = requests.length;
  const approvedCount = requests.filter(
    r => r.parsed_data.status === "Approved" || (r.parsed_data.staff_notes && r.parsed_data.staff_notes.includes("Auto-executed"))
  ).length;
  const pendingCount = requests.filter(
    r => r.parsed_data.status === "Pending" || r.parsed_data.status === "Pending Review"
  ).length;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "Lab Access":
        return <FlaskConical className="w-3.5 h-3.5 text-indigo-400" />;
      case "Maintenance & Repairs":
        return <Wrench className="w-3.5 h-3.5 text-rose-400" />;
      case "Facility Booking":
        return <CalendarDays className="w-3.5 h-3.5 text-cyan-400" />;
      case "Academic Request":
        return <GraduationCap className="w-3.5 h-3.5 text-emerald-400" />;
      case "IT & Equipment Support":
        return <Wifi className="w-3.5 h-3.5 text-purple-400" />;
      default:
        return <HelpCircle className="w-3.5 h-3.5 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Page Heading */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-white/5">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-400" />
            <span>My Requests</span>
          </h2>
          <p className="text-xs sm:text-sm text-gray-400 mt-0.5">
            Track and monitor the status of your submitted operational tickets and permissions in real-time.
          </p>
        </div>

        {/* Auto Refresh & Manual Sync */}
        <div className="flex items-center space-x-2">
          <label className="flex items-center space-x-2 text-xs text-gray-400 cursor-pointer bg-surface-50 px-3 py-1.5 rounded-xl border border-white/5">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded text-indigo-600 focus:ring-0"
            />
            <span>Live Sync (5s)</span>
          </label>

          <button
            type="button"
            onClick={loadData}
            className="p-2 rounded-xl bg-surface-50 hover:bg-surface-100 text-gray-300 border border-white/10 transition-colors"
            title="Refresh Requests Now"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-indigo-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* Student Metrics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Metric 1: Total */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Submitted</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl sm:text-3xl font-extrabold text-white">{totalRequests}</span>
            <span className="text-xs text-indigo-400 font-medium">Requests</span>
          </div>
        </div>

        {/* Metric 2: Pending */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Pending Review</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl sm:text-3xl font-extrabold text-amber-400">{pendingCount}</span>
            <span className="text-xs text-amber-400/80 font-medium">In Queue</span>
          </div>
        </div>

        {/* Metric 3: Approved */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Approved & Executed</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400">{approvedCount}</span>
            <span className="text-xs text-emerald-400 font-medium">Passes Issued</span>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-white/10">
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3">
          {/* Search */}
          <div className="sm:col-span-6 relative">
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search your requests by title, category, location, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl text-xs glass-input"
            />
          </div>

          {/* Category Filter */}
          <div className="sm:col-span-3">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-xl text-xs glass-input"
            >
              <option value="All">All Categories</option>
              <option value="Lab Access">Lab Access</option>
              <option value="Maintenance & Repairs">Maintenance & Repairs</option>
              <option value="Facility Booking">Facility Booking</option>
              <option value="Academic Request">Academic Request</option>
              <option value="IT & Equipment Support">IT & Equipment</option>
              <option value="General Inquiry">General Inquiry</option>
            </select>
          </div>

          {/* Priority Filter */}
          <div className="sm:col-span-3">
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="w-full px-3 py-2 rounded-xl text-xs glass-input"
            >
              <option value="All">All Priorities</option>
              <option value="Urgent">Urgent</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Requests Stream Cards */}
      <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden">
        {requests.length === 0 ? (
          <div className="py-16 text-center text-gray-500 space-y-2">
            <Activity className="w-8 h-8 mx-auto text-gray-600" />
            <p className="font-semibold text-sm text-gray-400">No requests found</p>
            <p className="text-xs text-gray-600">
              Submit requests via the Student Portal to track their approval status here.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {requests.map((item) => {
              const isExpanded = expandedRequestId === item.request_id;
              const p = item.parsed_data;
              const isApproved = p.status === "Approved" || (p.staff_notes && p.staff_notes.includes("Auto-executed"));

              return (
                <div 
                  key={item.request_id} 
                  className="p-4 sm:p-5 hover:bg-white/[0.02] transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    {/* Left: Badges + Title */}
                    <div className="space-y-1.5 flex-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="inline-flex items-center space-x-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-md bg-surface-100 text-gray-300 border border-white/10">
                          {getCategoryIcon(p.category)}
                          <span>{p.category}</span>
                        </span>

                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${
                          p.priority === "Urgent"
                            ? "bg-rose-500/15 text-rose-300 border-rose-500/30"
                            : p.priority === "High"
                            ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
                            : "bg-cyan-500/15 text-cyan-300 border-cyan-500/30"
                        }`}>
                          {p.priority}
                        </span>

                        {/* Status Badge */}
                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-md border ${
                          isApproved
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-sm"
                            : "bg-amber-500/15 text-amber-300 border-amber-500/30"
                        }`}>
                          {isApproved ? "Approved & Executed" : p.status}
                        </span>

                        {isApproved && (
                          <span className="inline-flex items-center space-x-1 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 animate-pulse">
                            <Zap className="w-3 h-3 text-cyan-400" />
                            <span>Gatepass Issued</span>
                          </span>
                        )}

                        <span className="text-[10px] text-gray-500 font-mono">
                          {formatTimeAgo(p.created_at || item.timestamp)}
                        </span>
                      </div>

                      <h4 className="font-bold text-white text-sm sm:text-base truncate">
                        {p.title}
                      </h4>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-400">
                        <span>
                          Student: <strong className="text-gray-200">{p.student_name}</strong> {p.student_id ? `(${p.student_id})` : ""}
                        </span>
                        {p.location && (
                          <>
                            <span>•</span>
                            <span>Location: <strong className="text-gray-200">{p.location}</strong></span>
                          </>
                        )}
                        {p.date_needed && (
                          <>
                            <span>•</span>
                            <span>Needed: <strong className="text-gray-200">{p.date_needed}</strong></span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Right: Toggle details only */}
                    <div className="flex items-center space-x-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => setExpandedRequestId(isExpanded ? null : item.request_id)}
                        className="p-2 rounded-xl bg-surface-50 hover:bg-surface-100 text-gray-400 hover:text-white transition-colors"
                        title="Toggle request details"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Expandable Details Drawer */}
                  {isExpanded && (
                    <div className="mt-4 pt-3 border-t border-white/5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs animate-fadeIn">
                      <div className="p-3 rounded-xl bg-surface-50 border border-white/5 space-y-1">
                        <span className="font-semibold text-gray-400 uppercase tracking-wider text-[10px]">
                          AI Summary & Extracted Details
                        </span>
                        <p className="text-gray-200 leading-relaxed">{p.summary}</p>
                      </div>

                      {p.staff_notes ? (
                        <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 space-y-1">
                          <span className="font-semibold text-emerald-400 uppercase tracking-wider text-[10px] flex items-center gap-1">
                            <ShieldCheck className="w-3 h-3" />
                            <span>Execution & Gatepass Info</span>
                          </span>
                          <p className="text-emerald-200 font-mono text-[11px] leading-relaxed">
                            {p.staff_notes}
                          </p>
                        </div>
                      ) : (
                        <div className="p-3 rounded-xl bg-surface-50 border border-white/5 space-y-1">
                          <span className="font-semibold text-gray-400 uppercase tracking-wider text-[10px]">
                            Original Request Text
                          </span>
                          <p className="text-gray-400 font-mono text-[11px] leading-relaxed italic">
                            "{p.raw_text}"
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
