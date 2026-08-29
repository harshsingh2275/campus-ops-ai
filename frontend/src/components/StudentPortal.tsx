"use client";

import React, { useState } from "react";
import { 
  Send, 
  Sparkles, 
  Building2, 
  DollarSign, 
  CalendarDays, 
  FlaskConical, 
  Wrench, 
  CheckCircle2, 
  ExternalLink, 
  Loader2, 
  AlertCircle, 
  Clock, 
  MapPin, 
  User,
  Hash, 
  ArrowRight,
  RefreshCw,
  BookOpen
} from "lucide-react";
import confetti from "canvas-confetti";
import { submitRequest, SubmitResponse, SubmitAuthError } from "@/lib/api";

interface PresetCategory {
  id: string;
  name: string;
  icon: React.ReactNode;
  badge: string;
  template: string;
  defaultId: string;
}

const PRESET_CATEGORIES: PresetCategory[] = [
  {
    id: "lab_access",
    name: "Lab Access",
    icon: <FlaskConical className="w-4 h-4 text-indigo-400" />,
    badge: "Robotics & Hardware",
    template: "Hi team, I need access to the Robotics Lab (Block B, Room 204) this Friday from 4 PM to 8 PM for our IEEE hardware project. My student ID is CS2024-042. Thanks!",
    defaultId: "CS2024-042",
  },
  {
    id: "hostel_leave",
    name: "Hostel Leave",
    icon: <Building2 className="w-4 h-4 text-emerald-400" />,
    badge: "Accommodation & Leave",
    template: "Requesting night outstation leave from Hostel Block C (Room 312) from Friday 6pm to Sunday 8pm to attend my sister's wedding in Bangalore. Emergency contact provided.",
    defaultId: "EC2023-118",
  },
  {
    id: "event_venue",
    name: "Event Venue",
    icon: <CalendarDays className="w-4 h-4 text-cyan-400" />,
    badge: "Auditorium & Grounds",
    template: "Urgent request to book the Main Auditorium on 15th September from 10 AM to 3 PM for the Annual Tech Fest Hackathon inauguration and guest lecture series.",
    defaultId: "ME2022-094",
  },
  {
    id: "budget_approval",
    name: "Budget Approval",
    icon: <DollarSign className="w-4 h-4 text-amber-400" />,
    badge: "Clubs & Projects",
    template: "Submitting requisition for reimbursement of ₹14,500 for IoT sensor modules and 3D printing filaments purchased for the Autonomous Rover University Competition. Invoices attached.",
    defaultId: "CS2023-501",
  },
  {
    id: "maintenance",
    name: "Maintenance & Repair",
    icon: <Wrench className="w-4 h-4 text-rose-400" />,
    badge: "Urgent Facilities",
    template: "URGENT: Water leakage from air conditioning duct in Hostel Block A Room 104. Water is dripping near electrical outlets. Please send emergency maintenance team immediately!",
    defaultId: "EE2024-303",
  },
  {
    id: "library_late_access",
    name: "Library Late Access",
    icon: <BookOpen className="w-4 h-4 text-violet-400" />,
    badge: "After-Hours Study",
    template: "Requesting late-night library access for Central Library (2nd Floor, Reading Hall) from 10 PM to 6 AM on weekdays for the next two weeks. Preparing for end-semester examinations and need a quiet study environment after regular hours.",
    defaultId: "IT2023-215",
  }
];

interface StudentPortalProps {
  onSuccessNavigate?: () => void;
}

export const StudentPortal: React.FC<StudentPortalProps> = ({ onSuccessNavigate }) => {
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [studentId, setStudentId] = useState("");
  const [rawText, setRawText] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isAuthError, setIsAuthError] = useState(false);
  const [submitResult, setSubmitResult] = useState<SubmitResponse | null>(null);

  const applyPreset = (preset: PresetCategory) => {
    setSelectedPreset(preset.id);
    setRawText(preset.template);
    setStudentId(preset.defaultId);
    setErrorMessage(null);
    setIsAuthError(false);
  };

  const handleReset = () => {
    setSelectedPreset(null);
    setRawText("");
    setStudentId("");
    setSubmitResult(null);
    setErrorMessage(null);
    setIsAuthError(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawText.trim() || rawText.trim().length < 8) {
      setErrorMessage("Please describe your request in at least 8 characters.");
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    setIsAuthError(false);

    try {
      const response = await submitRequest({
        raw_text: rawText.trim(),
        student_id: studentId.trim() || undefined,
        source: "web_portal"
      });

      setSubmitResult(response);
      
      // Fire confetti celebration
      try {
        confetti({
          particleCount: 80,
          spread: 60,
          origin: { y: 0.6 },
          colors: ["#6366f1", "#06b6d4", "#10b981", "#a855f7"]
        });
      } catch {}

    } catch (err: unknown) {
      // Distinguish auth errors from generic errors
      const authErr = err as SubmitAuthError;
      if (authErr?.code === "UNAUTHENTICATED" || authErr?.code === "SESSION_EXPIRED") {
        setIsAuthError(true);
        setErrorMessage(authErr.message);
      } else {
        setErrorMessage(
          (err as Error)?.message || "An unexpected error occurred while communicating with the server."
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl glass-panel p-6 sm:p-8 glow-bg border border-white/10">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Operations Ingestion Engine</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Student Request & Operational Ingestion Portal
          </h2>
          <p className="mt-2 text-sm sm:text-base text-gray-300">
            Submit your permissions, lab access requests, facility bookings, or maintenance queries in plain natural language. Our AI parser extracts structured parameters and syncs directly with Notion databases.
          </p>
        </div>
      </div>

      {/* Preset Category Templates */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
            <span>Quick-Fill Request Presets</span>
          </h3>
          <span className="text-xs text-gray-500">Click any preset to auto-populate template</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {PRESET_CATEGORIES.map((preset) => {
            const isSelected = selectedPreset === preset.id;
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => applyPreset(preset)}
                className={`flex flex-col items-start text-left p-3.5 rounded-xl border transition-all duration-300 ease-out ${
                  isSelected
                    ? "bg-indigo-950/60 border-indigo-500 text-white shadow-glow-brand ring-1 ring-indigo-500 scale-[1.02]"
                    : "glass-panel hover:scale-[1.02] hover:border-indigo-500 hover:shadow-lg hover:shadow-indigo-500/10 text-gray-300"
                }`}
              >
                <div className="p-2 rounded-lg bg-surface-50 border border-white/5 mb-2.5">
                  {preset.icon}
                </div>
                <div className="font-semibold text-sm text-white">{preset.name}</div>
                <div className="text-[11px] text-gray-400 mt-0.5">{preset.badge}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Request Form & Result Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Form Container */}
        <div className="lg:col-span-7">
          <form onSubmit={handleSubmit} className="glass-panel p-6 rounded-2xl border border-white/10 space-y-5 animate-fadeIn">
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <h3 className="font-semibold text-white text-base flex items-center gap-2">
                <Send className="w-4 h-4 text-indigo-400" />
                <span>Submit Request</span>
              </h3>
              {(rawText || studentId) && (
                <button
                  type="button"
                  onClick={handleReset}
                  className="text-xs text-gray-400 hover:text-gray-200 flex items-center gap-1 transition-colors"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Clear</span>
                </button>
              )}
            </div>

            {/* Student Identity — Roll Number only (name/email come from JWT) */}
            <div className="grid grid-cols-1 gap-3.5">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1.5 flex items-center gap-1">
                  <Hash className="w-3 h-3 text-cyan-400" />
                  <span>Student ID / Roll No</span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. CS2024-042"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl text-sm glass-input"
                />
              </div>
            </div>

            {/* Verified identity notice */}
            <p className="text-[11px] text-gray-500 flex items-center gap-1.5">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Your name and email are taken from your verified account and attached automatically.
            </p>

            {/* Unstructured Request Body */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-medium text-gray-300">
                  Unstructured Request Description <span className="text-rose-400">*</span>
                </label>
                <span className="text-[11px] text-gray-500">
                  {rawText.length} characters
                </span>
              </div>
              <textarea
                rows={5}
                required
                placeholder="Type or paste your natural language request here (e.g. 'I need access to Robotics Lab Room 204 this Friday from 4 PM to 8 PM for IEEE project work...')"
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
                className="w-full px-3.5 py-3 rounded-xl text-sm glass-input leading-relaxed resize-none"
              />
              <p className="text-[11px] text-gray-500 mt-1 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-indigo-400 inline" />
                <span>AI will automatically categorize, extract location, schedule dates, assign priority, and push to Notion.</span>
              </p>
            </div>

            {/* Error Display */}
            {errorMessage && (
              <div className={`p-3.5 rounded-xl border text-xs flex items-start space-x-2 ${
                isAuthError
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-300"
                  : "bg-rose-500/10 border-rose-500/30 text-rose-300"
              }`}>
                <AlertCircle className={`w-4 h-4 shrink-0 mt-0.5 ${isAuthError ? "text-amber-400" : "text-rose-400"}`} />
                <div className="flex-1">
                  {isAuthError ? (
                    <>
                      <span className="font-semibold block mb-1">Authentication Required</span>
                      <span>{errorMessage}</span>
                      <a
                        href="/login"
                        className="inline-flex items-center gap-1 mt-2 text-amber-300 underline underline-offset-2 hover:text-amber-200 transition-colors font-semibold"
                      >
                        Sign in to submit requests →
                      </a>
                    </>
                  ) : (
                    <>
                      <span className="font-semibold">Submission Failed:</span> {errorMessage}
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Submit Action Button */}
            <button
              type="submit"
              disabled={isSubmitting || !rawText.trim()}
              className="w-full py-3.5 px-4 rounded-xl font-semibold text-sm text-white bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 transition-all duration-200 shadow-glow-brand disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                  <span>Parsing & Syncing with Notion...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Submit to Campus Operations</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Success Output & AI Extracted Preview */}
        <div className="lg:col-span-5">
          {submitResult ? (
            <div className="glass-panel-elevated p-6 rounded-2xl border border-emerald-500/30 space-y-5 animate-scaleUp">
              {/* Header */}
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <div className="flex items-center space-x-2 text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-bold text-sm">Successfully Ingested!</span>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-surface-100 text-gray-400 border border-white/10">
                  {submitResult.request_id}
                </span>
              </div>

              {/* Title & Category */}
              <div>
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {submitResult.parsed_data.category}
                  </span>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-lg border ${
                    submitResult.parsed_data.priority === "Urgent"
                      ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                      : submitResult.parsed_data.priority === "High"
                      ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                      : "bg-cyan-500/20 text-cyan-300 border-cyan-500/30"
                  }`}>
                    {submitResult.parsed_data.priority} Priority
                  </span>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    {submitResult.parsed_data.status}
                  </span>
                </div>
                <h4 className="font-bold text-white text-base">
                  {submitResult.parsed_data.title}
                </h4>
              </div>

              {/* AI Summary */}
              <div className="p-3.5 rounded-xl bg-surface-50 border border-white/5 text-xs text-gray-300 space-y-1">
                <span className="font-semibold text-gray-400 block uppercase tracking-wider text-[10px]">
                  AI Extracted Summary
                </span>
                <p className="leading-relaxed text-gray-200">
                  {submitResult.parsed_data.summary}
                </p>
              </div>

              {/* Extracted Key Fields */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2.5 rounded-lg bg-surface-50/70 border border-white/5 flex items-center space-x-2">
                  <User className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <div className="truncate">
                    <span className="text-gray-400 block text-[10px]">Student</span>
                    <span className="font-medium text-white truncate">
                      {submitResult.parsed_data.student_name} ({submitResult.parsed_data.student_id || "No ID"})
                    </span>
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-surface-50/70 border border-white/5 flex items-center space-x-2">
                  <MapPin className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                  <div className="truncate">
                    <span className="text-gray-400 block text-[10px]">Location</span>
                    <span className="font-medium text-white truncate">
                      {submitResult.parsed_data.location || "Unspecified"}
                    </span>
                  </div>
                </div>

                <div className="p-2.5 rounded-lg bg-surface-50/70 border border-white/5 flex items-center space-x-2 col-span-2">
                  <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <div className="truncate">
                    <span className="text-gray-400 block text-[10px]">Execution / Schedule</span>
                    <span className="font-medium text-white truncate">
                      {submitResult.parsed_data.date_needed || "Immediate / Not Specified"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Notion Reference & Live Audit Navigation */}
              <div className="pt-2 space-y-2">
                {submitResult.notion_page_url && (
                  <a
                    href={submitResult.notion_page_url}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-2.5 px-3 rounded-xl bg-white/10 hover:bg-white/15 text-white font-medium text-xs flex items-center justify-center space-x-2 border border-white/10 transition-colors"
                  >
                    <span>View Formatted Page in Notion</span>
                    <ExternalLink className="w-3.5 h-3.5 text-indigo-300" />
                  </a>
                )}

                {onSuccessNavigate && (
                  <button
                    type="button"
                    onClick={onSuccessNavigate}
                    className="w-full py-2.5 px-3 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 font-medium text-xs flex items-center justify-center space-x-1.5 border border-indigo-500/30 transition-colors"
                  >
                    <span>View in Live Operations Dashboard</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[320px] rounded-2xl glass-panel p-6 border border-white/10 border-dashed flex flex-col items-center justify-center text-center text-gray-500 space-y-3">
              <div className="w-12 h-12 rounded-2xl bg-surface-50 flex items-center justify-center border border-white/5">
                <Sparkles className="w-6 h-6 text-indigo-400/50" />
              </div>
              <div className="max-w-xs">
                <h4 className="font-semibold text-gray-300 text-sm">Real-Time Extraction Preview</h4>
                <p className="text-xs text-gray-500 mt-1">
                  Once submitted, the AI parsed entity breakdown, priority badges, and direct Notion synchronization page will render here.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="pt-6 border-t border-white/5 text-center">
        <p className="text-sm text-gray-500">
          Built with <span className="text-gray-400">Next.js</span>, <span className="text-gray-400">FastAPI</span>, and <span className="text-gray-400">Notion</span> for the Hackathon
        </p>
      </div>
    </div>
  );
};
