"""
engine.py — Background Execution Engine for Campus Ops AI
==========================================================

This module implements the core automated execution loop that bridges the gap
between a *parsed request sitting in Notion* and a *real-world side-effect*
(gatepass file generation, terminal confirmation, audit logging).

## Notion Extraction Flow (end-to-end)

    ┌──────────────────────────────────────────────────────────┐
    │  1. Student submits a natural-language request via the   │
    │     frontend (/api/submit).                              │
    │  2. The submit route AI-parses the text, creates a       │
    │     structured Notion page in the Requests database      │
    │     with Status = "Pending".                             │
    │  3. A staff member manually changes Status → "Approved"  │
    │     in Notion.                                           │
    │  4. THIS ENGINE polls the Requests database every 10s:   │
    │     a. Searches all pages parented under the Requests DB │
    │     b. Filters for Status == "Approved"                  │
    │     c. Skips pages already processed (idempotency guard) │
    │     d. Extracts Student Name, Student ID, Title, and     │
    │        Category from Notion page properties              │
    │     e. Generates a digital gatepass (.txt file)          │
    │     f. Updates the Notion page's "Staff Notes" property  │
    │        to mark it as executed                            │
    │     g. Appends an ACTION_EXECUTION entry to the Notion   │
    │        Run Log database for full audit trail             │
    │  5. The in-memory request list is also updated so the    │
    │     frontend dashboard reflects changes in real time     │
    │     without requiring a full Notion re-query.            │
    └──────────────────────────────────────────────────────────┘

Key design decisions:
  - **Idempotency**: Each executed page ID is cached in ``_executed_page_ids``
    (in-memory set) AND the Staff Notes field is stamped so the engine never
    double-executes a ticket, even across restarts (the Staff Notes check
    survives because it reads Notion state).
  - **Dual-mode polling**: The engine polls both the live Notion API *and*
    the in-memory ``_processed_requests`` list so that it works correctly in
    both production (Notion configured) and local development (simulated).
"""

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from ..config import settings
from ..models.run_log import RunLogEventType, RunLogStatus
from .notion_service import notion_service, log_submission_event

logger = logging.getLogger("campus_ops.engine")


class ExecutionEngine:
    """
    Automated background poller and execution engine.
    Every 10 seconds, queries the Notion CampusOps Requests database for records
    where Status == 'Approved' and an execution flag has not yet been processed.
    Generates execution events, logs to Notion Run Log, and updates Notion Staff Notes.
    """

    def __init__(self, poll_interval_seconds: int = 10):
        """Initialise the engine with a configurable polling interval.

        Args:
            poll_interval_seconds: How frequently (in seconds) the engine
                queries Notion for newly-approved tickets. Defaults to 10.
        """
        self.poll_interval = poll_interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._is_running = False
        # In-memory set of Notion page IDs that have already been executed
        # during this server lifetime — provides fast O(1) idempotency checks
        # before the more expensive Staff Notes string comparison.
        self._executed_page_ids: set[str] = set()

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------

    def start(self):
        """Start the background polling task in asyncio event loop."""
        if self._is_running:
            return
        self._is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"ExecutionEngine background poller started (Interval: {self.poll_interval}s).")

    def stop(self):
        """Cancel and clean up the background poller task."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("ExecutionEngine background poller stopped.")

    # ------------------------------------------------------------------
    # Core polling loop
    # ------------------------------------------------------------------

    async def _poll_loop(self):
        """Infinite async loop: poll → execute → sleep → repeat.

        A 2-second initial delay prevents the engine from querying Notion
        before the rest of the FastAPI app has finished bootstrapping.
        """
        # Initial brief delay before starting periodic polling
        await asyncio.sleep(2)
        while self._is_running:
            try:
                await self.poll_and_execute()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during execution engine poll: {e}", exc_info=True)

            try:
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break

    # ------------------------------------------------------------------
    # Poll orchestrator
    # ------------------------------------------------------------------

    async def poll_and_execute(self):
        """Query Notion and in-memory repository for Approved tickets and execute them.

        Two data sources are checked on every tick:
          1. **Live Notion database** — the authoritative source when Notion
             credentials are configured (production mode).
          2. **In-memory request list** — ensures the engine also works in
             simulated/local-dev mode where Notion may not be connected.
        """
        # Avoid circular import with routes — the processed_requests list
        # lives in the submit module because the POST handler appends to it.
        from ..routes.submit import _processed_requests

        # 1. Query Live Notion Database if configured
        if settings.is_notion_configured and notion_service.client:
            await self._poll_notion_database(_processed_requests)

        # 2. Process in-memory records (for simulation/live synchronization)
        self._poll_in_memory_requests(_processed_requests)

    # ------------------------------------------------------------------
    # Notion database polling
    # ------------------------------------------------------------------

    async def _poll_notion_database(self, processed_requests: list):
        """Query the Notion Requests database for records with Status == 'Approved'.

        Extraction strategy:
          - Uses ``client.search()`` to retrieve all pages in the workspace
            (Notion's database query endpoint could also be used, but search
            lets us match by parent database without needing a separate filter
            object).
          - Each page's ``parent`` field is compared against the configured
            ``NOTION_REQUESTS_DATABASE_ID`` to ensure we only process pages
            belonging to the CampusOps Requests database.
          - Pages that have already been executed (present in
            ``_executed_page_ids`` or containing the engine stamp in Staff
            Notes) are skipped for idempotency.

        Args:
            processed_requests: The shared in-memory request list used for
                real-time frontend synchronization.
        """
        client = notion_service.client
        if not client:
            return

        try:
            # ── Step 1: Fetch all pages from the workspace ────────────
            search_res = client.search(filter={"value": "page", "property": "object"})
            results = search_res.get("results", [])

            # Normalise the target database ID (strip hyphens, lowercase)
            # so parent comparisons are format-agnostic.
            target_db_id = settings.NOTION_REQUESTS_DATABASE_ID.replace("-", "").lower()
            
            for page in results:
                page_id = page.get("id", "")
                parent_str = str(page.get("parent", {})).replace("-", "").lower()
                
                # ── Guard: skip pages not parented under our Requests DB
                if target_db_id not in parent_str:
                    continue

                # ── Guard: skip pages already executed this session
                if page_id in self._executed_page_ids:
                    continue

                props = page.get("properties", {})
                
                # ── Extract the Status property ──────────────────────
                # Notion represents status as either a "select" or a
                # newer "status" property type; we handle both.
                status_obj = props.get("Status", {}).get("select") or props.get("Status", {}).get("status") or {}
                status_name = status_obj.get("name", "") if isinstance(status_obj, dict) else ""
                
                # Only process tickets whose status is explicitly "Approved"
                if status_name.lower() != "approved":
                    continue

                # ── Idempotency: check Staff Notes for engine stamp ───
                # Even if _executed_page_ids missed it (e.g. server restart),
                # the presence of our stamp string in Staff Notes means
                # this ticket was already processed in a prior session.
                staff_notes_list = props.get("Staff Notes", {}).get("rich_text", [])
                staff_notes_text = "".join([t.get("plain_text", "") for t in staff_notes_list])
                
                if "Auto-executed by CampusOps Engine" in staff_notes_text:
                    self._executed_page_ids.add(page_id)
                    continue

                # ── Extract structured fields for execution ───────────
                # Pull Student Name, Student ID, Title, and Category from
                # the Notion page properties. These are used to populate
                # the gatepass file and audit log entry.
                student_name_list = props.get("Student Name", {}).get("rich_text", [])
                student_name = "".join([t.get("plain_text", "") for t in student_name_list]) or "Student"
                
                student_id_list = props.get("Student ID", {}).get("rich_text", [])
                student_id = "".join([t.get("plain_text", "") for t in student_id_list]) or "No ID"

                title_list = props.get("Title", {}).get("title", [])
                title = "".join([t.get("plain_text", "") for t in title_list]) or "Request"

                category_obj = props.get("Category", {}).get("select") or {}
                category = category_obj.get("name", "Operations Request")

                # ── Trigger execution for this approved ticket ────────
                await self._execute_ticket(
                    page_id=page_id,
                    student_name=student_name,
                    student_id=student_id,
                    title=title,
                    category=category,
                    processed_requests=processed_requests
                )

        except Exception as e:
            logger.warning(f"Notion poller query warning: {e}")

    # ------------------------------------------------------------------
    # Ticket execution
    # ------------------------------------------------------------------

    async def _execute_ticket(
        self,
        page_id: str,
        student_name: str,
        student_id: str,
        title: str,
        category: str,
        processed_requests: list
    ):
        """Execute action for an approved ticket, update Notion and Run Log.

        This is the *core side-effect* method. It:
          1. Generates a unique gatepass ID (``GP-2026-XXXXXX``).
          2. Calls ``_perform_external_action`` to write the .txt gatepass
             file to disk and print a terminal confirmation.
          3. Updates the originating Notion page's **Staff Notes** property
             with the engine execution stamp (prevents re-execution).
          4. Appends an ``ACTION_EXECUTION`` event to the Notion Run Log
             database for auditing.
          5. Synchronises the in-memory request record so the frontend
             dashboard reflects the update without a Notion re-query.

        Args:
            page_id:              Notion page UUID of the approved ticket.
            student_name:         Extracted student name for the gatepass.
            student_id:           Extracted student/roll ID.
            title:                Ticket title (for logging).
            category:             Request category (e.g. "Lab Access").
            processed_requests:   Shared in-memory list for frontend sync.
        """
        start_time = time.time()
        # Generate a unique gatepass identifier (hex suffix for uniqueness)
        pass_id = f"GP-2026-{uuid.uuid4().hex[:6].upper()}"
        now_utc = datetime.now(timezone.utc)
        now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # The stamp written into Notion Staff Notes — also serves as the
        # idempotency marker checked by ``_poll_notion_database``.
        staff_note_content = f"Auto-executed by CampusOps Engine on {now_str} (Digital Pass ID: {pass_id})"
        details_msg = f"Gatepass {pass_id} issued and dispatched for {student_name} ({student_id})"

        logger.info(f"⚡ [Execution Engine] Executing Approved Ticket '{title}' for {student_name} -> Pass: {pass_id}")

        # ── REAL-WORLD EXTERNAL ACTION ──────────────────────────────────
        # This is the part that makes something happen *outside* Notion.
        # It writes a physical .txt gatepass file to ``backend/gatepasses/``
        # and prints a terminal banner so operators get immediate feedback.
        gatepass_path = self._perform_external_action(
            student_name=student_name,
            student_id=student_id,
            category=category,
            pass_id=pass_id,
            now_str=now_str,
        )
        # ────────────────────────────────────────────────────────────────

        # ── Step 1: Write-back to Notion ────────────────────────────────
        # Update the original Request page's "Staff Notes" property so that
        # future polling cycles recognise this ticket as already executed.
        if settings.is_notion_configured and notion_service.client:
            try:
                notion_service.client.pages.update(
                    page_id=page_id,
                    properties={
                        "Staff Notes": {
                            "rich_text": [{"text": {"content": staff_note_content}}]
                        }
                    }
                )
                logger.info(f"Updated Notion page {page_id} with Staff Notes: {staff_note_content}")
            except Exception as e:
                logger.error(f"Failed updating Staff Notes on Notion page {page_id}: {e}")

        # ── Step 2: Append audit entry to Notion Run Log ────────────────
        # Every execution is recorded as an ACTION_EXECUTION event with
        # rich metadata so the operations dashboard can show a full timeline.
        elapsed_ms = (time.time() - start_time) * 1000
        log_submission_event(
            event_type=RunLogEventType.ACTION_EXECUTION,
            status=RunLogStatus.SUCCESS,
            details=details_msg,
            execution_time_ms=elapsed_ms,
            request_id=page_id,
            metadata={
                "action": "Gatepass Generation & Dispatch",
                "gatepass_id": pass_id,
                "student_name": student_name,
                "student_id": student_id,
                "category": category,
                "notion_page_id": page_id,
                "gatepass_file": str(gatepass_path),
            }
        )

        # Mark this page as executed so subsequent poll cycles skip it
        self._executed_page_ids.add(page_id)

        # ── Step 3: Sync in-memory request for frontend real-time view ──
        # Match by Notion page ID (normalised) or internal request ID,
        # then patch the record's status and staff notes so the Next.js
        # dashboard picks up the change on its next poll.
        clean_page_id = page_id.replace("-", "").lower()
        for req in processed_requests:
            req_notion_id = (req.notion_page_id or "").replace("-", "").lower()
            if req_notion_id == clean_page_id or req.request_id == page_id:
                req.parsed_data.status = "Approved"
                req.parsed_data.staff_notes = staff_note_content
                req.parsed_data.execution_id = pass_id

    # ------------------------------------------------------------------
    # External (real-world) side-effect
    # ------------------------------------------------------------------

    def _perform_external_action(
        self,
        student_name: str,
        student_id: str,
        category: str,
        pass_id: str,
        now_str: str,
    ) -> Path:
        """Produce a tangible, real-world artifact for an approved ticket.

        Two side-effects are performed:
          1. **Terminal confirmation** — a clearly visible SUCCESS banner is
             printed to stdout so operators monitoring the console see
             immediate feedback.
          2. **Gatepass file** — a human-readable ``.txt`` file is written to
             ``backend/gatepasses/`` containing the pass ID, student details,
             and issuance timestamp.

        Args:
            student_name: Full name of the student.
            student_id:   Institutional roll/ID number.
            category:     Request category (e.g. "Lab Access").
            pass_id:      Unique gatepass identifier (``GP-2026-XXXXXX``).
            now_str:      Human-readable UTC timestamp string.

        Returns:
            Path to the generated gatepass ``.txt`` file on disk.
        """
        # ── 1. Terminal confirmation ─────────────────────────────────
        print(
            f"\n{'='*60}\n"
            f"SUCCESS: External action triggered for {student_name} - {category}\n"
            f"{'='*60}\n"
        )

        # ── 2. Generate a real file on disk ──────────────────────────
        # Resolve the gatepasses directory relative to the backend root
        # (two parents up from this file: services/ → app/ → backend/).
        gatepasses_dir = Path(__file__).resolve().parent.parent.parent / "gatepasses"
        gatepasses_dir.mkdir(parents=True, exist_ok=True)

        # Sanitise the student ID for safe filesystem usage
        safe_id = student_id.replace("/", "-").replace("\\", "-").replace(" ", "_")
        filename = f"Approved_Gatepass_{safe_id}.txt"
        filepath = gatepasses_dir / filename

        content = (
            f"{'='*50}\n"
            f"  CAMPUS OPS AI — APPROVED DIGITAL GATEPASS\n"
            f"{'='*50}\n\n"
            f"  Pass ID      : {pass_id}\n"
            f"  Student Name : {student_name}\n"
            f"  Student ID   : {student_id}\n"
            f"  Category     : {category}\n"
            f"  Issued At    : {now_str}\n\n"
            f"  This is an auto-generated gatepass for {student_name}.\n\n"
            f"{'='*50}\n"
            f"  Generated by CampusOps AI Execution Engine\n"
            f"{'='*50}\n"
        )
        filepath.write_text(content, encoding="utf-8")

        logger.info(f"📄 Gatepass file written to: {filepath}")
        return filepath
    # ─────────────────────────────────────────────────────────────────

    # ------------------------------------------------------------------
    # In-memory fallback polling
    # ------------------------------------------------------------------

    def _poll_in_memory_requests(self, processed_requests: list):
        """Process any in-memory request marked Approved that hasn't been executed yet.

        This method handles the simulation/local-dev path where Notion may not
        be connected. It iterates over the shared ``processed_requests`` list
        and executes any record whose status is "Approved" but whose
        ``staff_notes`` field is still empty (i.e. not yet stamped by the
        engine).

        Args:
            processed_requests: The shared in-memory list of submitted
                requests, populated by the ``/api/submit`` route handler.
        """
        for req in processed_requests:
            # Only act on Approved tickets that haven't been stamped yet
            if req.parsed_data.status == "Approved" and not req.parsed_data.staff_notes:
                pass_id = f"GP-2026-{uuid.uuid4().hex[:6].upper()}"
                now_utc = datetime.now(timezone.utc)
                now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

                # ── Real-world external action ───────────────────────
                # Same gatepass generation + terminal print as the
                # Notion-backed path, ensuring parity between modes.
                self._perform_external_action(
                    student_name=req.parsed_data.student_name,
                    student_id=req.parsed_data.student_id or "No_ID",
                    category=req.parsed_data.category,
                    pass_id=pass_id,
                    now_str=now_str,
                )
                # ─────────────────────────────────────────────────────

                # Stamp the in-memory record to prevent re-execution
                req.parsed_data.staff_notes = f"Auto-executed by CampusOps Engine on {now_str} (Digital Pass ID: {pass_id})"
                req.parsed_data.execution_id = pass_id
                
                # Append an audit trail entry to the Notion Run Log
                log_submission_event(
                    event_type=RunLogEventType.ACTION_EXECUTION,
                    status=RunLogStatus.SUCCESS,
                    details=f"Gatepass {pass_id} issued and dispatched for {req.parsed_data.student_name} ({req.parsed_data.student_id or 'No ID'})",
                    execution_time_ms=1.5,
                    request_id=req.request_id,
                    metadata={
                        "action": "Gatepass Dispatch",
                        "gatepass_id": pass_id,
                        "student_name": req.parsed_data.student_name,
                        "category": req.parsed_data.category
                    }
                )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
# A single ``ExecutionEngine`` instance is created at import time and shared
# across the application. ``main.py`` calls ``.start()`` / ``.stop()`` on
# this instance during the FastAPI lifespan.
# ---------------------------------------------------------------------------
execution_engine = ExecutionEngine(poll_interval_seconds=10)
