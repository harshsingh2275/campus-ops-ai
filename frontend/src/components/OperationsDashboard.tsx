"use client";

import React, { useState, useEffect } from "react";
import { 
  Activity, 
  Search, 
  Filter, 
  RefreshCw, 
  ExternalLink, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  ChevronDown, 
  ChevronUp, 
  Database, 
  Zap, 
  ShieldCheck, 
  AlertCircle,
  FlaskConical,
  Wrench,
  CalendarDays,
  DollarSign,
  GraduationCap,
  Wifi,
  HelpCircle,
  FileText,
  Check,
  Loader2,
  Ticket
} from "lucide-react";
import { 
  fetchRequests, 
  fetchLogs, 
  approveRequest,
  SubmitResponse, 
  RunLogEntry, 
  HealthResponse 
} from "@/lib/api";
import { formatTimeAgo } from "@/lib/utils";

interface OperationsDashboardProps {
  health: HealthResponse | null;
}

export const OperationsDashboard: React.FC<OperationsDashboardProps> = ({ health }) => {
  const [requests, setRequests] = useState<SubmitResponse[]>([]);
  const [logs, setLogs] = useState<RunLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedPriority, setSelectedPriority] = useState("All");
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedRequestId, setExpandedRequestId] = useState<string | null>(null);
  const [activeSubTab, setActiveSubTab] = useState<"requests" | "audit">("requests");
  const [approvingId, setApprovingId] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [reqData, logData] = await Promise.all([
        fetchRequests({
          category: selectedCategory !== "All" ? selectedCategory : undefined,
          priority: selectedPriority !== "All" ? selectedPriority : undefined,
          search: searchQuery || undefined,
        }),
        fetchLogs(50),
      ]);
      setRequests(reqData);
      setLogs(logData);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (requestId: string) => {
    setApprovingId(requestId);
    try {
      await approveRequest(requestId);
      await loadData();
    } catch (err) {
      console.error("Failed approving request:", err);
    } finally {
      setApprovingId(null);
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

  // Compute Metrics
  const totalRequests = requests.length;
  const approvedCount = requests.filter(r => r.parsed_data.status === "Approved" || (r.parsed_data.staff_notes && r.parsed_data.staff_notes.includes("Auto-executed"))).length;
  const actionExecutionsCount = logs.filter(l => l.event_type === "Action Execution").length;
  const avgDuration = logs.length > 0
    ? (logs.reduce((acc, curr) => acc + curr.execution_time_ms, 0) / logs.length).toFixed(1)
    : "0.0";

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
      {/* Top Metrics Banner */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Total Ingested</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl sm:text-3xl font-extrabold text-white">{totalRequests}</span>
            <span className="text-xs text-indigo-400 font-medium">Tickets</span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Auto-Executed Passes</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Ticket className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl sm:text-3xl font-extrabold text-emerald-400">{approvedCount}</span>
            <span className="text-xs text-emerald-400 font-medium">Dispatched</span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Engine Actions</span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl sm:text-3xl font-extrabold text-cyan-300">{actionExecutionsCount}</span>
            <span className="text-xs text-gray-400 font-medium">Poll 10s</span>
          </div>
        </div>

        {/* Metric 4 */}
        <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-white/10 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">Notion Engine</span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-2xl sm:text-3xl font-extrabold text-white">Live</span>
            <span className="text-xs text-emerald-400 font-medium">Sync Active</span>
          </div>
        </div>
      </div>

      {/* Control Bar & Sub-Tab Switcher */}
      <div className="glass-panel p-4 rounded-2xl border border-white/10 space-y-4">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Sub-Tab Navigation */}
          <div className="flex items-center bg-surface-50 p-1 rounded-xl border border-white/5">
            <button
              onClick={() => setActiveSubTab("requests")}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeSubTab === "requests"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Requests Stream ({requests.length})</span>
            </button>
            <button
              onClick={() => setActiveSubTab("audit")}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeSubTab === "audit"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>Notion Run Log ({logs.length})</span>
            </button>
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
              <span>Live Poll (5s)</span>
            </label>

            <button
              type="button"
              onClick={loadData}
              className="p-2 rounded-xl bg-surface-50 hover:bg-surface-100 text-gray-300 border border-white/10 transition-colors"
              title="Refresh Data Now"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-indigo-400" : ""}`} />
            </button>
          </div>
        </div>

        {/* Search and Filters (Active for Requests tab) */}
        {activeSubTab === "requests" && (
          <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 pt-2 border-t border-white/5">
            {/* Search */}
            <div className="sm:col-span-6 relative">
              <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search requests by title, student, ID, location, or summary..."
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
        )}
      </div>

      {/* Main Content Area */}
      {activeSubTab === "requests" ? (
        /* Requests Table / Cards */
        <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden">
          {requests.length === 0 ? (
            <div className="py-16 text-center text-gray-500 space-y-2">
              <Activity className="w-8 h-8 mx-auto text-gray-600" />
              <p className="font-semibold text-sm text-gray-400">No requests match the current criteria</p>
              <p className="text-xs text-gray-600">Submit requests via the Student Portal to see them stream live here.</p>
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

                      {/* Right: Actions */}
                      <div className="flex items-center space-x-2 shrink-0">
                        {!isApproved && (
                          <button
                            type="button"
                            disabled={approvingId === item.request_id}
                            onClick={() => handleApprove(item.request_id)}
                            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 text-xs font-semibold border border-emerald-500/30 transition-all shadow-sm"
                            title="Approve ticket and trigger automated pass dispatch"
                          >
                            {approvingId === item.request_id ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Check className="w-3.5 h-3.5" />
                            )}
                            <span>Approve & Dispatch</span>
                          </button>
                        )}

                        {item.notion_page_url && (
                          <a
                            href={item.notion_page_url}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-xs text-indigo-300 border border-white/10 transition-colors"
                          >
                            <span>Notion Page</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}

                        <button
                          type="button"
                          onClick={() => setExpandedRequestId(isExpanded ? null : item.request_id)}
                          className="p-1.5 rounded-xl bg-surface-50 hover:bg-surface-100 text-gray-400 transition-colors"
                          title="Toggle summary details"
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
                            AI Summary & Findings
                          </span>
                          <p className="text-gray-200 leading-relaxed">{p.summary}</p>
                        </div>

                        {p.staff_notes ? (
                          <div className="p-3 rounded-xl bg-emerald-950/30 border border-emerald-500/30 space-y-1">
                            <span className="font-semibold text-emerald-400 uppercase tracking-wider text-[10px] flex items-center gap-1">
                              <ShieldCheck className="w-3 h-3" />
                              <span>Notion Staff Notes (Execution Engine)</span>
                            </span>
                            <p className="text-emerald-200 font-mono text-[11px] leading-relaxed">
                              {p.staff_notes}
                            </p>
                          </div>
                        ) : (
                          <div className="p-3 rounded-xl bg-surface-50 border border-white/5 space-y-1">
                            <span className="font-semibold text-gray-400 uppercase tracking-wider text-[10px]">
                              Original Raw Student Text
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
      ) : (
        /* Notion Run Log Execution Audit Table */
        <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden">
          <div className="p-4 border-b border-white/5 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-white text-sm">Notion Run Log Execution Trace</h3>
              <p className="text-xs text-gray-400">Microsecond pipeline traces & automated action executions synced to Notion Run Log DB.</p>
            </div>
            <span className="text-xs text-gray-400 font-mono">
              {logs.length} Total Events
            </span>
          </div>

          {logs.length === 0 ? (
            <div className="py-16 text-center text-gray-500">
              <Database className="w-8 h-8 mx-auto text-gray-600 mb-2" />
              <p className="text-sm">No run log events captured yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-50/80 text-gray-400 uppercase text-[10px] tracking-wider border-b border-white/5">
                  <tr>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Event Type</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Duration</th>
                    <th className="px-4 py-3">Request ID</th>
                    <th className="px-4 py-3">Trace Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {logs.map((log) => {
                    const isActionExec = log.event_type === "Action Execution";
                    return (
                      <tr 
                        key={log.id} 
                        className={`hover:bg-white/[0.02] transition-colors ${
                          isActionExec ? "bg-emerald-950/20" : ""
                        }`}
                      >
                        <td className="px-4 py-3 text-gray-400 font-mono whitespace-nowrap">
                          {formatTimeAgo(log.created_at)}
                        </td>
                        <td className="px-4 py-3 font-semibold text-gray-200">
                          {isActionExec ? (
                            <span className="inline-flex items-center space-x-1.5 text-cyan-300">
                              <Zap className="w-3.5 h-3.5 text-cyan-400" />
                              <span>{log.event_type}</span>
                            </span>
                          ) : (
                            <span>{log.event_type}</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            log.status === "Success"
                              ? "bg-emerald-500/15 text-emerald-400"
                              : log.status === "Failure"
                              ? "bg-rose-500/15 text-rose-400"
                              : "bg-amber-500/15 text-amber-400"
                          }`}>
                            {log.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-mono text-cyan-400 whitespace-nowrap">
                          {log.execution_time_ms.toFixed(1)} ms
                        </td>
                        <td className="px-4 py-3 font-mono text-gray-400 whitespace-nowrap">
                          {log.request_id || "—"}
                        </td>
                        <td className="px-4 py-3 text-gray-300 max-w-md truncate" title={log.details}>
                          {log.details}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
