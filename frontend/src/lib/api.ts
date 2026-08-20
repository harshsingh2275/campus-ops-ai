export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StudentRequestInput {
  raw_text: string;
  student_name?: string;
  student_id?: string;
  email?: string;
  source?: string;
}

export interface ParsedStudentRequest {
  title: string;
  student_name: string;
  student_id?: string | null;
  email?: string | null;
  category: string;
  priority: "Low" | "Medium" | "High" | "Urgent" | string;
  status: string;
  location?: string | null;
  summary: string;
  urgency: string;
  date_needed?: string | null;
  staff_notes?: string | null;
  execution_id?: string | null;
  raw_text: string;
  extracted_metadata: Record<string, any>;
  created_at: string;
}

export interface SubmitResponse {
  success: boolean;
  message: string;
  request_id: string;
  parsed_data: ParsedStudentRequest;
  notion_page_id?: string | null;
  notion_page_url?: string | null;
  run_log_id?: string | null;
  mode: "live" | "simulated" | "live_fallback" | string;
  timestamp: string;
}

export interface RunLogEntry {
  id: string;
  event_name: string;
  event_type: string;
  status: "Success" | "Failure" | "Warning" | "In Progress" | string;
  request_id?: string | null;
  execution_time_ms: number;
  details: string;
  error_message?: string | null;
  metadata: Record<string, any>;
  notion_page_id?: string | null;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  notion: {
    configured: boolean;
    requests_db_set: boolean;
    run_log_db_set: boolean;
    mode: string;
  };
  cors: {
    allowed_origins: string[];
  };
}

export async function submitRequest(payload: StudentRequestInput): Promise<SubmitResponse> {
  const res = await fetch(`${API_BASE_URL}/api/submit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail?.message || `Submission failed with status ${res.status}`);
  }

  return res.json();
}

export async function approveRequest(requestId: string): Promise<SubmitResponse> {
  const res = await fetch(`${API_BASE_URL}/api/requests/${requestId}/approve`, {
    method: "POST",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail?.message || `Approval failed with status ${res.status}`);
  }

  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/health`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchLogs(limit: number = 30): Promise<RunLogEntry[]> {
  const res = await fetch(`${API_BASE_URL}/api/logs?limit=${limit}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch logs: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchRequests(params?: {
  category?: string;
  priority?: string;
  search?: string;
  limit?: number;
}): Promise<SubmitResponse[]> {
  const url = new URL(`${API_BASE_URL}/api/requests`);
  if (params?.category && params.category !== "All") url.searchParams.append("category", params.category);
  if (params?.priority && params.priority !== "All") url.searchParams.append("priority", params.priority);
  if (params?.search) url.searchParams.append("search", params.search);
  if (params?.limit) url.searchParams.append("limit", params.limit.toString());

  const res = await fetch(url.toString(), {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch requests: ${res.statusText}`);
  }
  return res.json();
}
