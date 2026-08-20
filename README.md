<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js_14-000000?style=for-the-badge&logo=nextdotjs&logoColor=white" />
  <img src="https://img.shields.io/badge/Notion_API-000000?style=for-the-badge&logo=notion&logoColor=white" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
</p>

# 🏫 CampusOps AI

> **An intelligent, end-to-end campus operations automation system that turns unstructured student requests into structured Notion workflows — and then _acts on them_ in the real world.**

CampusOps AI accepts free-form text requests from students (hostel leave, lab access, facility bookings, maintenance), parses them with rule-based NLP, pushes structured records into a Notion database, and runs a **background execution engine** that automatically detects approved tickets and generates real-world artifacts like digital gatepasses.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧠 **Smart NLP Parser** | Rule-based entity extraction pulls Student ID, Name, Category, Priority, Location, and Date/Time from free-form text — no LLM API needed |
| 📝 **Notion as the Backend DB** | Every request becomes a fully formatted page in your Notion `CampusOps Requests` database with live status tracking |
| 📊 **Run Log Audit Trail** | Every system event (ingestion, execution, startup) is logged to a separate Notion `Run Log` database for full observability |
| ⚡ **Automated Execution Engine** | A 10-second background poller detects `Status == "Approved"` tickets in Notion and triggers real-world actions automatically |
| 📄 **Real-World Artifact Generation** | When a ticket is approved, the engine generates an `Approved_Gatepass_[StudentID].txt` file on disk — satisfying the "if nothing changes in the real world, you built a dashboard" rule |
| 🎨 **Modern Dashboard UI** | Next.js 14 + Tailwind CSS frontend with a Student Submission Portal and a Live Operations & Audit Dashboard |
| 🔄 **Live Polling** | The frontend auto-refreshes every 5 seconds, showing request status changes, execution events, and KPI metrics in real time |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 14)                    │
│  ┌──────────────────────┐   ┌────────────────────────────────┐  │
│  │  Student Submission   │   │  Live Operations & Audit       │  │
│  │  Portal (Tab 1)       │   │  Dashboard (Tab 2)             │  │
│  │  • 5 preset templates │   │  • KPI cards & status badges   │  │
│  │  • Auto-validation    │   │  • Search/filter table         │  │
│  │  • Confetti feedback  │   │  • Approve & Dispatch button   │  │
│  └──────────┬───────────┘   │  • Run Log trace viewer        │  │
│             │               └──────────┬─────────────────────┘  │
│             │  POST /api/submit        │  GET /api/requests      │
│             │                          │  GET /api/logs          │
└─────────────┼──────────────────────────┼────────────────────────┘
              │                          │
              ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  NLP Parser  │  │ Notion Svc   │  │  Execution Engine      │  │
│  │  • Category  │  │ • Pages API  │  │  • 10s background poll │  │
│  │  • Priority  │──│ • Run Log    │──│  • Auto-detect Approved│  │
│  │  • Student ID│  │ • Staff Notes│  │  • Generate gatepass   │  │
│  │  • Location  │  │ • Status     │  │  • Write .txt to disk  │  │
│  └─────────────┘  └──────┬───────┘  └──────────┬─────────────┘  │
│                          │                     │                │
└──────────────────────────┼─────────────────────┼────────────────┘
                           │                     │
                           ▼                     ▼
              ┌────────────────────┐   ┌──────────────────┐
              │   Notion Databases │   │  Real-World       │
              │  • CampusOps       │   │  Artifacts        │
              │    Requests        │   │  • Gatepass .txt   │
              │  • Run Log         │   │  • Terminal logs   │
              └────────────────────┘   └──────────────────┘
```

---

## 📂 Project Structure

```
campus-ops-ai/
├── .env.example                  # Environment variable template
├── .gitignore
├── README.md
│
├── backend/                      # FastAPI Python backend
│   ├── requirements.txt
│   ├── gatepasses/               # Auto-generated gatepass files (real-world output)
│   │   └── Approved_Gatepass_ME2024-445.txt
│   ├── app/
│   │   ├── main.py               # FastAPI app entrypoint + lifespan hooks
│   │   ├── config.py             # Pydantic Settings (env vars, Notion config)
│   │   ├── models/
│   │   │   ├── request.py        # Pydantic models for student requests
│   │   │   └── run_log.py        # Run Log event types & status enums
│   │   ├── routes/
│   │   │   ├── submit.py         # POST /api/submit, GET /api/requests, POST /api/requests/{id}/approve
│   │   │   └── health.py         # GET /api/health, GET /api/logs
│   │   └── services/
│   │       ├── parser.py         # Rule-based NLP entity extractor
│   │       ├── notion_service.py # Notion API client (pages, run log)
│   │       └── engine.py         # Background execution engine + external actions
│   └── tests/
│       ├── test_api.py           # 7 pytest tests (health, parser, e2e submit)
│       ├── verify_engine.py      # Integration test: poller + Notion update
│       └── verify_external_action.py  # Integration test: file generation
│
└── frontend/                     # Next.js 14 App Router frontend
    ├── package.json
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── layout.tsx        # Root layout with Inter font
        │   ├── page.tsx          # Main page with tab switching
        │   └── globals.css       # Global styles + Tailwind
        ├── components/
        │   ├── Navbar.tsx        # Top nav with health indicator
        │   ├── StudentPortal.tsx # Submission form with templates
        │   └── OperationsDashboard.tsx  # Live ops table + KPI cards
        └── lib/
            └── api.ts            # Typed API client (submit, approve, fetch)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- A **Notion Integration** with access to two databases

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/campus-ops-ai.git
cd campus-ops-ai
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
NOTION_API_KEY=ntn_your_integration_secret_here
NOTION_REQUESTS_DATABASE_ID=your_32_char_hex_id
NOTION_RUN_LOG_DATABASE_ID=your_32_char_hex_id
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### 3. Set Up Notion Databases

Create two databases in Notion and share them with your integration:

**CampusOps Requests** database with these properties:

| Property | Type |
|---|---|
| `Title` | Title |
| `Student Name` | Rich Text |
| `Student ID` | Rich Text |
| `Category` | Select (`Lab Access`, `Maintenance & Repairs`, `Facility Booking`, `Academic Request`, `IT & Equipment Support`, `Event Approval`, `General Inquiry`) |
| `Priority` | Select (`Low`, `Medium`, `High`, `Urgent`) |
| `Status` | Select (`Pending Review`, `Approved`, `In Review`, `Rejected`, `Completed`) |
| `AI Summary` | Rich Text |
| `Staff Notes` | Rich Text |
| `Risk Flag` | Checkbox |

**Run Log** database with these properties:

| Property | Type |
|---|---|
| `Run` | Title |
| `Event` | Select (`Request Ingestion`, `Action Execution`, `System Startup`) |
| `Status` | Select (`Success`, `Failure`, `Warning`) |
| `Timestamp` | Date |
| `Request ID` | Rich Text |
| `Details` | Rich Text |

### 4. Start the Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

You should see:
```
INFO: Notion Live Configured: True
INFO: ExecutionEngine background poller started (Interval: 10s).
INFO: Uvicorn running on http://127.0.0.1:8000
```

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check with Notion connection status |
| `POST` | `/api/submit` | Parse unstructured text → create Notion page + Run Log entry |
| `GET` | `/api/requests` | List submitted requests (supports `?category=`, `?priority=`, `?search=`) |
| `GET` | `/api/logs?limit=50` | Fetch Run Log entries |
| `POST` | `/api/requests/{id}/approve` | Approve a request and trigger execution engine |

### Example: Submit a Request

```bash
curl -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Need lab access to Robotics Lab Room 204 on Friday 4pm-8pm. Student ID: CS2024-042.",
    "student_name": "Alex Kumar"
  }'
```

**Response:**
```json
{
  "success": true,
  "request_id": "req_a1b2c3d4",
  "parsed_data": {
    "title": "[Lab Access] Robotics Lab (CS2024-042)",
    "category": "Lab Access",
    "priority": "Medium",
    "student_id": "CS2024-042",
    "location": "Robotics Lab",
    "status": "Pending"
  },
  "notion_page_id": "3c2bff8a-...",
  "mode": "live"
}
```

---

## ⚡ Execution Engine — Real-World Actions

The background engine runs every **10 seconds** and does the following when it detects an approved ticket:

1. **Prints to terminal:**
   ```
   ============================================================
   SUCCESS: External action triggered for Ankit Verma - Lab Access
   ============================================================
   ```

2. **Generates a gatepass file** at `backend/gatepasses/Approved_Gatepass_[StudentID].txt`:
   ```
   ==================================================
     CAMPUS OPS AI — APPROVED DIGITAL GATEPASS
   ==================================================

     Pass ID      : GP-2026-19717B
     Student Name : Ankit Verma
     Student ID   : ME2024-445
     Category     : Lab Access
     Issued At    : 2026-08-20 20:42:51 UTC

     This is an auto-generated gatepass for Ankit Verma.

   ==================================================
     Generated by CampusOps AI Execution Engine
   ==================================================
   ```

3. **Writes a success row** to the Notion Run Log database with event type `Action Execution`.

4. **Updates the Notion page** `Staff Notes` field with:
   `Auto-executed by CampusOps Engine on [timestamp] (Digital Pass ID: GP-2026-XXXXXX)`

---

## 🧪 Testing

### Unit Tests (7 tests)

```bash
cd backend
python -m pytest tests/test_api.py -v
```

```
tests/test_api.py::test_health_check            PASSED
tests/test_api.py::test_root                     PASSED
tests/test_api.py::test_parser_lab_access        PASSED
tests/test_api.py::test_parser_maintenance_urgent PASSED
tests/test_api.py::test_parser_facility_booking  PASSED
tests/test_api.py::test_submit_route_end_to_end  PASSED
tests/test_api.py::test_logs_endpoint            PASSED
```

### Integration Tests (requires running server + Notion)

```bash
# Test the full execution engine pipeline
python tests/verify_engine.py

# Test real-world file generation
python tests/verify_external_action.py
```

---

## 🧠 NLP Parser Categories

The parser uses weighted keyword matching across **6 categories** plus a fallback:

| Category | Example Triggers |
|---|---|
| **Lab Access** | `lab`, `robotics`, `workbench`, `equipment access`, `after-hours` |
| **Maintenance & Repairs** | `broken`, `leaking`, `AC`, `plumbing`, `short circuit` |
| **Facility Booking** | `auditorium`, `seminar hall`, `book the room`, `venue reservation` |
| **Academic Request** | `assignment extension`, `attendance`, `re-evaluation`, `transcript` |
| **IT & Equipment Support** | `Wi-Fi`, `projector`, `password reset`, `printer` |
| **Event Approval** | `hackathon`, `workshop`, `club event`, `budget approval` |
| **General Inquiry** | _(fallback when no category matches)_ |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.12, FastAPI, Pydantic v2, Uvicorn |
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
| **Database** | Notion API (official `notion-client` SDK) |
| **NLP** | Rule-based regex parser (zero external API dependencies) |
| **Testing** | pytest, FastAPI TestClient |
| **UI Libraries** | Lucide React (icons), canvas-confetti, clsx, tailwind-merge |

---

## 📄 License

This project was built for the Notion hackathon. Feel free to fork and adapt.

---

<p align="center">
  Built with ☕ and the <a href="https://developers.notion.com/">Notion API</a>
</p>
