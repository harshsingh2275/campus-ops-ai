```markdown
# TASK.md

## Project: CampusOps AI
### An Autonomous College Administrative Workflow Portal powered by Notion (Dual-Database Architecture)

---

## 0. Mission Statement

You are an autonomous coding agent operating inside Google Antigravity. Your task is to **scaffold, implement, connect, run, and self-verify** a full-stack hackathon prototype called **CampusOps AI** — a workflow portal where students submit administrative requests (hostel leave, event venue booking, lab access, budget approval), which get auto-categorized and prioritized by a lightweight intelligence layer, stored in **Notion** as the system of record, and tracked live on a dashboard.

This system uses **two separate Notion databases**: one for the actual student requests (**CampusOps Requests**), and one as an immutable audit trail of every system action (**Run Log**). Every meaningful backend operation — ticket creation, ticket creation failure, approval-triggered automation — must produce a corresponding **Run Log** entry. This audit trail is a first-class requirement, not an afterthought.

Do not stop at partial implementation. Do not ask the human for clarification unless a credential is genuinely missing at runtime — in that case, halt cleanly with an explicit error message rather than mocking around it silently. Every phase below has a **Definition of Done**. Do not proceed to the next phase until the current phase's Definition of Done is met.

---

## 1. System Architecture

```
CampusOps-AI/
├── .env                          # Root secrets (see §2)
├── .gitignore
├── README.md
├── start.sh                      # Convenience script: boots backend + frontend
│
├── backend/
│   ├── venv/                     # Python virtual environment (created at setup)
│   ├── requirements.txt
│   ├── main.py                   # FastAPI app entrypoint, CORS, router mounting
│   ├── config.py                 # Loads .env, exposes settings object
│   ├── models/
│   │   └── schemas.py            # Pydantic models: RequestSubmit, RequestOut, RunLogEntry, etc.
│   ├── services/
│   │   ├── notion_requests.py    # Notion API wrapper for the CampusOps Requests DB
│   │   ├── notion_runlog.py      # Notion API wrapper for the Run Log DB
│   │   ├── intelligence.py       # Categorization, priority, risk-flag engine
│   │   └── actions.py            # Simulated post-approval actions
│   ├── routers/
│   │   └── requests.py           # /api/requests/* endpoints
│   └── tests/
│       └── test_intelligence.py  # Unit tests for the rule engine
│
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.ts
    ├── postcss.config.js
    ├── tsconfig.json
    ├── .env.local                # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
    └── app/
        ├── layout.tsx
        ├── globals.css
        ├── page.tsx               # Landing / tab switcher (Submit | Dashboard)
        ├── components/
        │   ├── Navbar.tsx
        │   ├── SubmissionForm.tsx
        │   ├── StatusPill.tsx
        │   ├── PriorityTag.tsx
        │   ├── RequestCard.tsx
        │   └── Dashboard.tsx
        └── lib/
            └── api.ts             # fetch wrappers for backend endpoints
```

**Definition of Done (Phase 0):** The full directory tree above exists on disk, empty files/stubs acceptable at this stage, before any logic is written.

---

## 2. Environment Configuration

### 2.1 Root `.env` (create in project root; backend loads via `python-dotenv`)

```env
NOTION_API_KEY=secret_xxx_replace_me
NOTION_REQUESTS_DB_ID=xxx_replace_me
NOTION_RUNLOG_DB_ID=xxx_replace_me
PORT=8000
FRONTEND_ORIGIN=http://localhost:3000
ENVIRONMENT=development
```

- The agent must create this `.env` file with **placeholder values** if it does not already exist, and print a clear terminal warning that real Notion credentials must be inserted before the backend can successfully write to Notion.
- The agent must **never** hardcode credentials in source files. All secrets flow through `config.py` (backend) via `os.getenv`.
- If `NOTION_API_KEY`, `NOTION_REQUESTS_DB_ID`, or `NOTION_RUNLOG_DB_ID` are missing or still placeholders at server startup, `main.py` must log a loud warning banner but still boot the server (so the frontend and mocked flows remain testable).

### 2.2 Frontend `.env.local`

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 3. Notion Database Property Schemas

The agent must document (in `README.md`) and **defensively code against** the following exact Notion schemas for **both** databases. Assume the human has manually created both Notion databases and shared them with the integration; the agent does not need to create the databases itself, but the payload-builder functions must map to these exact property names and types.

### 3.1 Database 1 — `CampusOps Requests` (`NOTION_REQUESTS_DB_ID`)

| Property Name  | Notion Type | Allowed Values / Notes                                                                                          |
|-----------------|------------|--------------------------------------------------------------------------------------------------------------------|
| `Title`         | `title`     | Human-readable summary, e.g. "Hostel Leave – Aditi Sharma"                                                        |
| `Student Name`  | `rich_text` | Free text                                                                                                          |
| `Student ID`    | `rich_text` | Free text                                                                                                          |
| `Category`      | `select`    | `Hostel Leave`, `Budget Approval`, `Event Venue`, `Lab Access`                                                    |
| `AI Summary`    | `rich_text` | Auto-generated one-line summary from the intelligence layer                                                       |
| `Priority`      | `select`    | `P1-Urgent`, `P2-Normal`, `P3-Low`                                                                                 |
| `Risk Flag`     | `checkbox`  | `true`/`false` — set by rule engine (e.g. late submission, budget over threshold, flagged keywords)               |
| `Status`        | `select`    | `Pending Review`, `Approved`, `Rejected`, `Processing`, `Completed`, `Needs Human Review`, `Failed` (default: `Pending Review`) |
| `Staff Notes`   | `rich_text` | Editable by staff directly in Notion; read back by `GET /api/requests`                                            |

Payload shape for page creation:

```python
{
  "parent": {"database_id": NOTION_REQUESTS_DB_ID},
  "properties": {
    "Title": {"title": [{"text": {"content": title_str}}]},
    "Student Name": {"rich_text": [{"text": {"content": student_name}}]},
    "Student ID": {"rich_text": [{"text": {"content": student_id}}]},
    "Category": {"select": {"name": category}},
    "AI Summary": {"rich_text": [{"text": {"content": ai_summary}}]},
    "Priority": {"select": {"name": priority}},
    "Risk Flag": {"checkbox": risk_flag_bool},
    "Status": {"select": {"name": "Pending Review"}},
    "Staff Notes": {"rich_text": []}
  }
}
```

### 3.2 Database 2 — `Run Log` (`NOTION_RUNLOG_DB_ID`)

| Property Name | Notion Type | Allowed Values / Notes                                                                 |
|----------------|------------|-------------------------------------------------------------------------------------------|
| `Run`          | `title`     | Short label, e.g. `"submit:CS21B045:2026-08-21T10:32:00"` or `"poll-actions:batch-4"`     |
| `Timestamp`    | `date`      | ISO 8601 datetime of the event                                                            |
| `Event`        | `rich_text` or `select` | e.g. `ticket_created`, `ticket_create_failed`, `approval_action_executed`, `poll_cycle_run` |
| `Request ID`   | `rich_text` | The related `CampusOps Requests` page ID (empty string if not applicable, e.g. a poll cycle with zero results) |
| `Details`      | `rich_text` | Free-text description — what happened, any error message, any mock action output          |
| `Status`       | `select`    | `Success`, `Pending`, `Failed`                                                            |

Payload shape for page creation:

```python
{
  "parent": {"database_id": NOTION_RUNLOG_DB_ID},
  "properties": {
    "Run": {"title": [{"text": {"content": run_label}}]},
    "Timestamp": {"date": {"start": iso_timestamp}},
    "Event": {"rich_text": [{"text": {"content": event_name}}]},
    "Request ID": {"rich_text": [{"text": {"content": request_id_str}}]},
    "Details": {"rich_text": [{"text": {"content": details_str}}]},
    "Status": {"select": {"name": status_str}}
  }
}
```

> If the human's actual `Event` property is configured as `select` rather than `rich_text` in their Notion workspace, `notion_runlog.py` must detect the property type via `client.databases.retrieve(database_id=...)` at startup (cached in memory) and format the payload accordingly (`{"select": {"name": event_name}}` vs `{"rich_text": [...]}`), so the same code works against either configuration without crashing.

**Definition of Done (Phase 0 schema):** `notion_requests.py` and `notion_runlog.py` each contain a payload builder and a response-normalizer function that converts a raw Notion page object back into a flat JSON dict (`RequestOut` / `RunLogEntry`), correctly extracting values out of Notion's nested property structure with safe fallbacks (empty string / `None` / `False`) if a property is missing or empty. `notion_runlog.py` exposes a single reusable function `write_log(event: str, request_id: str, details: str, status: str) -> dict` that every other service calls — no duplicated Run Log payload-building logic anywhere else in the codebase.

---

## 4. Phase 1 — Environment & Setup

Execute the following, without interactive prompts blocking execution (use `-y` / non-interactive flags wherever applicable):

```bash
# From project root
mkdir -p backend frontend

# --- Backend ---
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install fastapi "uvicorn[standard]" pydantic python-dotenv notion-client requests python-multipart
pip freeze > requirements.txt
deactivate
cd ..

# --- Frontend ---
cd frontend
npx --yes create-next-app@latest . --typescript --tailwind --eslint --app --src-dir=false --import-alias "@/*" --use-npm --no-interactive
npm install lucide-react
cd ..
```

- If `create-next-app` prompts interactively despite flags, the agent must pass `--yes` to `npx` and accept all defaults programmatically (e.g., pipe `yes ""` or use documented non-interactive flags for the installed version).
- Create root `.env` per §2.1 if absent.
- Create `frontend/.env.local` per §2.2.
- Create a root `start.sh`:

```bash
#!/usr/bin/env bash
set -e
( cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000 ) &
( cd frontend && npm run dev ) &
wait
```

Make it executable: `chmod +x start.sh`.

**Definition of Done (Phase 1):** `backend/venv` exists with FastAPI/Uvicorn/notion-client installed; `frontend/` is a working Next.js 14+ App Router project with Tailwind and lucide-react installed; `.env` and `.env.local` exist; `start.sh` is executable.

---

## 5. Phase 2 — FastAPI Backend Engine (`/backend`)

### 5.1 Pydantic Models (`models/schemas.py`)

```python
from pydantic import BaseModel
from typing import Optional, Literal

class RequestSubmit(BaseModel):
    student_name: str
    student_id: str
    category: Literal["Hostel Leave", "Budget Approval", "Event Venue", "Lab Access"]
    description: str
    requested_amount: Optional[float] = None   # relevant for Budget Approval
    requested_date: Optional[str] = None        # ISO date, relevant for Hostel Leave / Event Venue / Lab Access

class RequestOut(BaseModel):
    notion_page_id: str
    title: str
    student_name: str
    student_id: str
    category: str
    ai_summary: str
    priority: str
    risk_flag: bool
    status: str
    staff_notes: Optional[str] = ""

class RunLogEntry(BaseModel):
    notion_page_id: Optional[str] = None
    run: str
    timestamp: str
    event: str
    request_id: str
    details: str
    status: Literal["Success", "Pending", "Failed"]
```

### 5.2 Intelligence Layer (`services/intelligence.py`)

Implement a **pure, testable, rule-based function**:

```python
def analyze_request(payload: RequestSubmit) -> dict:
    """
    Returns: {
        "ai_summary": str,
        "priority": "P1-Urgent" | "P2-Normal" | "P3-Low",
        "risk_flag": bool
    }
    """
```

Rules (implement all; keep logic explicit, no black-box LLM dependency required — LLM call is optional/pluggable):

- **AI Summary**: Template-generate a one-line summary, e.g. `f"{category} request from {student_name} ({student_id}): {description[:80]}"`.
- **Priority logic**:
  - `Budget Approval` where `requested_amount > 10000` → `P1-Urgent`
  - `Hostel Leave` where description contains urgency keywords (`emergency`, `medical`, `urgent`, `family emergency`) → `P1-Urgent`
  - `Lab Access` or `Event Venue` requested within next 24–48 hours (compare `requested_date` to now) → `P2-Normal` minimum, escalate to `P1-Urgent` if within 24 hours
  - Default → `P2-Normal`
  - Low-stakes / informational requests (short description, no amount, far-future date) → `P3-Low`
- **Risk Flag** (`true` if any):
  - `Budget Approval` amount exceeds a configurable threshold (e.g. ₹10,000)
  - Requested date is in the past or same-day (suspiciously last-minute)
  - Description contains flagged keywords (`alcohol`, `party`, `unauthorized`, `overnight`, `off-campus`) — case-insensitive substring match
  - Missing/empty `student_id` (should be blocked at validation, but flag defensively too)

Design this as a **strategy dictionary keyed by category** internally so it's easy to extend, but expose only the single `analyze_request` function.

### 5.3 Notion Client Services

**`services/notion_requests.py`** — wraps the `CampusOps Requests` database:
- Instantiate a single `notion_client.Client` from `NOTION_API_KEY`, shared/imported by both this module and `notion_runlog.py` (do not create duplicate client instances).
- `create_ticket(payload: RequestSubmit, analysis: dict) -> dict`: builds the payload per §3.1, calls `client.pages.create(...)`, returns the raw Notion response.
- `query_tickets(page_size: int = 50) -> list[dict]`: calls `client.databases.query(database_id=NOTION_REQUESTS_DB_ID, sorts=[{"timestamp": "created_time", "direction": "descending"}], page_size=page_size)`, returns raw results list.
- `query_approved_tickets() -> list[dict]`: filters server-side (Notion API `filter` param) for `Status == "Approved"`.
- `update_ticket_status(page_id: str, status: str) -> dict`: used by the poll-actions flow to transition `Approved` → `Processing`/`Completed`.
- `normalize_page(page: dict) -> RequestOut`: converts a raw Notion page object into the flat `RequestOut` shape, with defensive `.get()` chains so a missing/empty property never throws.
- All Notion calls wrapped in `try/except`; on failure, re-raise as `HTTPException(status_code=502, detail=...)` **and** call `notion_runlog.write_log(event="ticket_create_failed", ...)` before re-raising, so failures are audited too, not just successes.

**`services/notion_runlog.py`** — wraps the `Run Log` database:
- `write_log(event: str, request_id: str, details: str, status: Literal["Success","Pending","Failed"]) -> dict`: builds the payload per §3.2 (including the property-type auto-detection noted there), calls `client.pages.create(...)`, returns the raw Notion response. This function must **never raise** — if the Run Log write itself fails, catch the exception and `print()`/log it loudly to the console instead, so a broken audit trail never takes down the primary request flow.
- `query_recent_logs(page_size: int = 50) -> list[dict]`: optional helper, useful for debugging/verification, queries `NOTION_RUNLOG_DB_ID` sorted newest-first.
- `normalize_log_page(page: dict) -> RunLogEntry`: same defensive normalization pattern as `notion_requests.normalize_page`.

### 5.4 Routers (`routers/requests.py`)

**`POST /api/requests/submit`**
1. Accept `RequestSubmit` JSON body.
2. Validate via Pydantic (FastAPI does this automatically; return 422 on failure).
3. Call `analyze_request(payload)`.
4. Call `notion_requests.create_ticket(payload, analysis)`.
   - **On success:** call `notion_runlog.write_log(event="ticket_created", request_id=<new_page_id>, details=f"Created {category} ticket, priority={priority}", status="Success")`.
   - **On failure:** call `notion_runlog.write_log(event="ticket_create_failed", request_id="", details=<error message>, status="Failed")`, then propagate the `HTTPException`.
5. Normalize the response and return `RequestOut` with HTTP 201.

**`GET /api/requests`**
1. Optional query params: `status: Optional[str]`, `category: Optional[str]`, `limit: int = 50`.
2. Call `notion_requests.query_tickets(limit)`.
3. Normalize every page into `RequestOut`.
4. Apply optional client-side filtering by `status`/`category` if provided.
5. Return `list[RequestOut]`, sorted newest-first.
6. This endpoint does **not** write to the Run Log (read-only, high-frequency polling from the dashboard — logging every poll would flood the audit trail).

**`POST /api/requests/poll-actions`**
1. Call `notion_requests.query_approved_tickets()`.
2. Maintain a local dedupe ledger (`backend/processed_actions.json`) of page IDs already actioned, so re-running this endpoint doesn't double-process.
3. For each newly-approved, not-yet-processed ticket:
   - Optionally transition `Status` → `Processing` via `notion_requests.update_ticket_status(...)`.
   - Simulate the downstream action based on category (terminal print + returned string):
     - `Hostel Leave` → mock gatepass confirmation
     - `Event Venue` → mock venue confirmation slip
     - `Lab Access` → mock access-slip
     - `Budget Approval` → mock disbursement confirmation
   - Transition `Status` → `Completed`.
   - Call `notion_runlog.write_log(event="approval_action_executed", request_id=<page_id>, details=<mock output string>, status="Success")`.
   - Append the page ID to `processed_actions.json`.
4. If a ticket fails mid-processing (Notion update error, etc.), transition it to `Needs Human Review` or `Failed` as appropriate, and log `event="approval_action_failed"`, `status="Failed"` with the error detail.
5. Always call one summary-level `notion_runlog.write_log(event="poll_cycle_run", request_id="", details=f"Processed {n} tickets, {m} already done", status="Success")` at the end of the cycle, even if `n == 0` — this proves the polling mechanism itself is alive, distinct from any individual ticket action.
6. Return `{"processed": [...], "already_done": [...]}`.

### 5.5 `main.py`

- Instantiate `FastAPI(title="CampusOps AI Backend")`.
- Add `CORSMiddleware` allowing origin `http://localhost:3000` (read from `FRONTEND_ORIGIN` env var), methods `["*"]`, headers `["*"]`.
- Include the `requests` router under prefix `/api/requests`.
- Add a root `GET /health` returning `{"status": "ok"}` for quick liveness checks.
- Startup event: log whether all three Notion env vars (`NOTION_API_KEY`, `NOTION_REQUESTS_DB_ID`, `NOTION_RUNLOG_DB_ID`) look configured (non-placeholder) or not, individually — a human debugging a half-configured `.env` needs to know exactly which one is missing.

**Definition of Done (Phase 2):** `uvicorn main:app --port 8000` boots without error; `GET /health` returns 200; `POST /api/requests/submit` with a valid payload either successfully creates a page in **both** the Requests DB and the Run Log DB (if real credentials are present) or returns a clear 502 error naming the Notion failure while still attempting a Run Log write documenting the failure — it must never silently crash or return a raw unhandled traceback.

---

## 6. Phase 3 — Next.js Frontend (`/frontend`)

### 6.1 Layout & Navigation

- `app/layout.tsx`: root layout, imports `globals.css`, sets page metadata (`CampusOps AI`), wraps children in a shared `<Navbar />` and centered max-width container.
- `app/page.tsx`: client component holding an `activeTab` state (`"submit" | "dashboard"`), rendering a two-tab switcher (styled pill/segmented control using Tailwind + lucide-react icons — `ClipboardList` for submit, `LayoutDashboard` for dashboard) and conditionally rendering `<SubmissionForm />` or `<Dashboard />`.

### 6.2 Student Submission Portal (`components/SubmissionForm.tsx`)

- Fields:
  - Student Name (text, required)
  - Student ID (text, required)
  - Category (select, required — matches Notion `select` options exactly: `Hostel Leave`, `Budget Approval`, `Event Venue`, `Lab Access`)
  - Description (textarea, required, min length validation)
  - Requested Amount (number, shown conditionally when Category === "Budget Approval")
  - Requested Date (date picker, shown conditionally for Hostel Leave / Event Venue / Lab Access)
- Client-side validation: required fields non-empty, amount > 0 if present, date not in the past for future-dated categories. Show inline error messages, disable submit button while invalid.
- On submit: `POST` to `${NEXT_PUBLIC_API_BASE_URL}/api/requests/submit` via `lib/api.ts`.
- Show a loading spinner state during submission, then an instant success confirmation card (displaying returned `priority`, `risk_flag`, `ai_summary`) or a clear error toast/banner on failure.
- Reset form after successful submission.

### 6.3 Live Tracking Dashboard (`components/Dashboard.tsx`)

- On mount (and on a manual "Refresh" button + optional 15s polling interval), `GET` from `${NEXT_PUBLIC_API_BASE_URL}/api/requests`.
- Render results as a responsive grid/list of `<RequestCard />`, each showing:
  - Title, Student Name, Student ID, Category badge
  - `<StatusPill />` — color-coded across all seven statuses: `Pending Review` = amber, `Approved` = green, `Rejected` = red, `Processing` = blue (pulsing/animated), `Completed` = teal, `Needs Human Review` = orange, `Failed` = dark red
  - `<PriorityTag />` — color-coded: `P1-Urgent` = red, `P2-Normal` = blue, `P3-Low` = gray
  - Risk flag indicator (warning icon from lucide-react, e.g. `AlertTriangle`) shown only if `risk_flag === true`
  - AI Summary text
  - Staff Notes (read-only display)
- Include simple client-side filter controls (by Category, by Status) above the grid.
- Empty state ("No requests yet") and loading skeleton state must both be implemented — no blank/broken screens.

### 6.4 `lib/api.ts`

Centralize all fetch calls:

```typescript
export async function submitRequest(payload: RequestSubmitPayload): Promise<RequestOut> { ... }
export async function fetchRequests(filters?: { status?: string; category?: string }): Promise<RequestOut[]> { ... }
```

- Read base URL from `process.env.NEXT_PUBLIC_API_BASE_URL`.
- Throw descriptive errors on non-2xx responses so UI components can catch and display them.

### 6.5 Styling

- Tailwind CSS throughout, clean modern aesthetic (rounded-xl cards, soft shadows, generous spacing, a coherent accent color for CampusOps AI branding).
- Fully responsive: mobile-first form, dashboard grid collapses to single column on small screens.

**Definition of Done (Phase 3):** `npm run dev` boots the frontend on port 3000 without build errors; both tabs render; submitting the form triggers a real network call to the backend; the dashboard renders live data across all status states (or a clean empty/error state if the backend/Notion isn't reachable).

---

## 7. Phase 4 — Execution & Verification

### 7.1 Startup Commands

```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev

# OR, from project root:
./start.sh
```

### 7.2 Self-Verification Checklist (agent MUST execute all of these before declaring the task complete)

1. **Backend health check**
   ```bash
   curl -s http://localhost:8000/health
   ```
   Expect: `{"status":"ok"}`

2. **CORS sanity check** — confirm response headers from a GET/OPTIONS request to `/api/requests` include `Access-Control-Allow-Origin: http://localhost:3000`.

3. **Submit endpoint (happy path) — verify dual-database write**
   ```bash
   curl -s -X POST http://localhost:8000/api/requests/submit \
     -H "Content-Type: application/json" \
     -d '{
           "student_name": "Aditi Sharma",
           "student_id": "CS21B045",
           "category": "Hostel Leave",
           "description": "Family emergency, need to leave campus tonight",
           "requested_date": "2026-08-21"
         }'
   ```
   Expect: HTTP 201, JSON body with `priority: "P1-Urgent"`, `risk_flag` boolean present, `notion_page_id` non-empty.
   **Then**, separately confirm a matching entry appeared in the **Run Log** database (via `notion_runlog.query_recent_logs()` — expose this temporarily through a debug script or a `GET /api/debug/runlog` endpoint if helpful — `event="ticket_created"`, `status="Success"`, `request_id` matching the page ID just returned).
   If credentials are placeholders, expect a clean 502 with a descriptive Notion-auth error, and confirm the Run Log **still** received a `ticket_create_failed` / `status="Failed"` entry — this is an acceptable terminal state to report, NOT a silent failure.

4. **Submit endpoint (validation)** — POST with a missing required field, expect HTTP 422 (no Notion writes attempted, no Run Log entry).

5. **List endpoint**
   ```bash
   curl -s http://localhost:8000/api/requests
   ```
   Expect: HTTP 200, JSON array (possibly empty), each item matching `RequestOut` shape.

6. **Poll-actions endpoint**
   ```bash
   curl -s -X POST http://localhost:8000/api/requests/poll-actions
   ```
   Expect: HTTP 200, JSON with `processed` and `already_done` arrays. Confirm a `poll_cycle_run` entry lands in the Run Log regardless of whether any tickets were approved. If at least one ticket was manually set to `Approved` in Notion before this call, confirm its `Status` transitions to `Completed` and a matching `approval_action_executed` Run Log entry exists.

7. **Frontend build check**
   ```bash
   cd frontend && npm run build
   ```
   Expect: build completes with zero errors (warnings acceptable).

8. **Frontend browser sub-agent check** (if browser tooling is available):
   - Load `http://localhost:3000`
   - Confirm both tabs render and are clickable
   - Fill and submit the Student Submission Portal form with sample data
   - Confirm a success confirmation appears
   - Switch to Live Tracking Dashboard, confirm the new request appears with the correct status pill and priority tag (or confirm a clean, styled error state if Notion isn't actually configured — never a raw stack trace or blank white screen)

9. **Report state honestly**: if `NOTION_API_KEY`, `NOTION_REQUESTS_DB_ID`, or `NOTION_RUNLOG_DB_ID` are still placeholders, the agent must clearly state in its final summary — per-variable — which are stubbed, rather than claiming full end-to-end success across both databases.

**Definition of Done (Phase 4 / overall task complete):** All checklist items 1–7 pass (or fail only due to documented missing Notion credentials, never due to code bugs), item 8 is attempted if browser tooling exists, and every code path that touches the Requests database (success or failure) has a demonstrably corresponding Run Log entry. The agent produces a final summary listing what works, what is blocked on credentials, and the exact commands the human needs to run to supply real Notion credentials for both databases and fully activate the system.

---

## 8. Non-Negotiable Engineering Standards

- No hardcoded secrets anywhere in source.
- No silent `except: pass` blocks — all exceptions logged and surfaced as clean HTTP errors, and audited to the Run Log wherever they touch the Requests database.
- All API responses are typed/validated via Pydantic; no raw dict returns from routers.
- The Run Log write path (`notion_runlog.write_log`) must be fail-safe: an error while writing to the Run Log itself must **never** propagate and break the primary user-facing request — log to console as a last resort.
- Frontend never shows a raw JS error or blank screen — every async state (loading/empty/error/success) is explicitly handled.
- Code must be idiomatic for its ecosystem: PEP8-ish for Python, standard Next.js App Router conventions for TypeScript/React.
- README.md must be updated with setup instructions, both Notion schema tables from §3, and the verification checklist from §7.2, so a human judge can run this project cold.
```