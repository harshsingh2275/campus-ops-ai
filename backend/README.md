# Campus Ops AI - Backend Service

High-performance FastAPI service that ingests unstructured student requests, parses them into operational schema entities using intelligent NLP extraction, pushes formatted pages and rich content blocks to Notion Requests database, and logs every ingestion/execution event to the Notion Run Log database.

## Architecture

```
backend/
├── app/
│   ├── main.py              # FastAPI app lifecycle, CORS, route registration
│   ├── config.py            # Pydantic Settings & environment loader
│   ├── models/
│   │   ├── request.py       # Pydantic models for Student Requests
│   │   └── run_log.py       # Pydantic models for Notion Run Log
│   ├── services/
│   │   ├── parser.py        # Natural Language & Heuristic Request Parser
│   │   └── notion_service.py # Official notion-client SDK wrapper & Run Logger
│   └── routes/
│       ├── submit.py        # POST /api/submit endpoint
│       └── health.py        # GET /api/health & GET /api/logs
├── tests/
│   ├── test_api.py          # Pytest unit & integration test suite
│   └── verify_live.py       # Live HTTP end-to-end verification script
└── requirements.txt
```

## Setup & Running

### 1. Configure Environment (`.env`)
```bash
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Notion API credentials
NOTION_API_KEY=secret_your_notion_api_token
NOTION_REQUESTS_DATABASE_ID=your_requests_database_id
NOTION_RUN_LOG_DATABASE_ID=your_run_log_database_id
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Start the Server
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### 1. `POST /api/submit`
Accepts unstructured student requests, parses entities, pushes to Notion Requests DB, and records in Run Log DB.

**Request Payload:**
```json
{
  "raw_text": "Hi, I need access to the Robotics Lab (Block B, Room 204) this Friday from 4 PM to 8 PM. My student ID is CS2024-042 and email is alex@campus.edu.",
  "student_name": "Alex Kumar"
}
```

**Response Payload (`200 OK`):**
```json
{
  "success": true,
  "message": "Student request parsed and pushed to Notion successfully.",
  "request_id": "req_40dc30af",
  "parsed_data": {
    "title": "[Lab Access] Block B, Room 204 (CS2024-042)",
    "student_name": "Alex Kumar",
    "student_id": "CS2024-042",
    "email": "alex@campus.edu",
    "category": "Lab Access",
    "priority": "Urgent",
    "status": "Pending",
    "location": "Block B, Room 204",
    "summary": "Hi, I need access to the Robotics Lab (Block B, Room 204) this Friday from 4 PM to 8 PM...",
    "urgency": "Urgent",
    "date_needed": "this Friday from 4 PM to 8 PM",
    "raw_text": "...",
    "extracted_metadata": { ... }
  },
  "notion_page_id": "...",
  "notion_page_url": "...",
  "run_log_id": "log_35c38468d1",
  "mode": "live"
}
```

### 2. `GET /api/health`
Health check and Notion connection status inspection.

### 3. `GET /api/logs`
Retrieves recent run log events.

### 4. Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
