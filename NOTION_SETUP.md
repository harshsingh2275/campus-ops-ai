# 📋 Notion Database Setup Guide — CampusOps AI

> Quick reference for creating the two Notion databases that CampusOps AI connects to.
> Column names and property types **must match exactly** — the backend code references them by name.

---

## 🔑 Environment Variables

Add these to your `.env` file (in the project root or `backend/` directory):

```env
NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_REQUESTS_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_RUN_LOG_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

| Variable | Aliases Accepted | Description |
|---|---|---|
| `NOTION_API_KEY` | `NOTION_TOKEN` | Your Notion integration's Internal Integration Secret |
| `NOTION_REQUESTS_DATABASE_ID` | `NOTION_REQUESTS_DB_ID` | Database ID of the **Requests** database |
| `NOTION_RUN_LOG_DATABASE_ID` | `NOTION_RUNLOG_DB_ID` | Database ID of the **Run Log** database |

> [!TIP]
> You can find a database ID from its Notion URL:
> `https://notion.so/your-workspace/<DATABASE_ID>?v=...`

---

## 📦 Database 1: CampusOps Requests

This is the primary database where AI-parsed student requests are stored.

| Column Name | Notion Property Type | Required | Description |
|---|---|---|---|
| **Title** | `Title` | ✅ Yes | Auto-generated request title (max 100 chars) |
| **Student Name** | `Rich text` | ✅ Yes | Full name of the requesting student |
| **Student ID** | `Rich text` | Optional | Student roll number / ID (e.g. `CS2024-042`) |
| **Category** | `Select` | ✅ Yes | Request category (auto-classified by the AI parser) |
| **Priority** | `Select` | ✅ Yes | Priority level assigned by the AI parser |
| **Status** | `Select` | ✅ Yes | Current workflow status of the request |
| **AI Summary** | `Rich text` | ✅ Yes | AI-generated summary of the request (max 1900 chars) |
| **Risk Flag** | `Checkbox` | ✅ Yes | Checked automatically when Priority is `Urgent` or `High` |
| **Staff Notes** | `Rich text` | ✅ Yes | Written by the Execution Engine after auto-execution |

### Select Option Values

These are the values the backend writes into Select columns. Notion will auto-create them on first use, but you can pre-populate them for cleaner colours:

**Category** options:
- `Lab Access`
- `Hostel Leave`
- `Event Venue`
- `Budget Approval`
- `Maintenance & Repair`
- `Library Access`
- `Operations Request` *(fallback)*

**Priority** options:
- `Urgent`
- `High`
- `Medium`
- `Low`

**Status** options:
- `Pending Review` *(initial state set on ingestion)*
- `Approved` *(set by staff — triggers the Execution Engine)*
- `Rejected`
- `In Progress`

---

## 📊 Database 2: Run Log

This is the audit trail database where every system event (startup, submission, execution) is recorded.

| Column Name | Notion Property Type | Required | Description |
|---|---|---|---|
| **Run** | `Title` | ✅ Yes | Event name string (e.g. `[SUBMISSION] SUCCESS - req_abc123`) |
| **Event** | `Select` | ✅ Yes | Event type category |
| **Status** | `Select` | ✅ Yes | Outcome status of the event |
| **Timestamp** | `Date` | ✅ Yes | ISO 8601 UTC timestamp of when the event occurred |
| **Details** | `Rich text` | ✅ Yes | Human-readable description (max 1900 chars) |
| **Request ID** | `Rich text` | Optional | Links the log entry back to a specific request |

### Select Option Values

**Event** options:
- `SYSTEM_STARTUP`
- `SUBMISSION`
- `ACTION_EXECUTION`

**Status** options:
- `SUCCESS`
- `FAILURE`

---

## 🔗 Notion Integration Setup

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) and create an **Internal Integration**.
2. Copy the **Internal Integration Secret** → set as `NOTION_API_KEY`.
3. Create both databases in your Notion workspace with the columns listed above.
4. **Share each database** with your integration (click `•••` → `Connections` → select your integration).
5. Copy each database ID from its URL → set as `NOTION_REQUESTS_DATABASE_ID` and `NOTION_RUN_LOG_DATABASE_ID`.

> [!IMPORTANT]
> Both databases **must** be shared with the integration. If you forget this step, the backend will fall back to simulated mode and log a warning.

---

## ✅ Verification

Once configured, restart the backend and check the terminal output:

```
Starting Campus Ops AI Backend v1.0.0
Notion Live Configured: True
```

The system will also create a `SYSTEM_STARTUP` entry in your Run Log database on every boot, confirming the connection is live.
