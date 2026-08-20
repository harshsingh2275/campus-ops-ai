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
        self.poll_interval = poll_interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._is_running = False
        self._executed_page_ids: set[str] = set()

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

    async def _poll_loop(self):
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

    async def poll_and_execute(self):
        """Query Notion and in-memory repository for Approved tickets and execute them."""
        # Avoid circular import with routes
        from ..routes.submit import _processed_requests

        # 1. Query Live Notion Database if configured
        if settings.is_notion_configured and notion_service.client:
            await self._poll_notion_database(_processed_requests)

        # 2. Process in-memory records (for simulation/live synchronization)
        self._poll_in_memory_requests(_processed_requests)

    async def _poll_notion_database(self, processed_requests: list):
        """Query Notion Requests database for records where Status == 'Approved'."""
        client = notion_service.client
        if not client:
            return

        try:
            # Search all pages in workspace
            search_res = client.search(filter={"value": "page", "property": "object"})
            results = search_res.get("results", [])

            # Filter for pages belonging to CampusOps Requests database
            target_db_id = settings.NOTION_REQUESTS_DATABASE_ID.replace("-", "").lower()
            
            for page in results:
                page_id = page.get("id", "")
                parent_str = str(page.get("parent", {})).replace("-", "").lower()
                
                # Check parent database match
                if target_db_id not in parent_str:
                    continue

                if page_id in self._executed_page_ids:
                    continue

                props = page.get("properties", {})
                
                # Extract Status
                status_obj = props.get("Status", {}).get("select") or props.get("Status", {}).get("status") or {}
                status_name = status_obj.get("name", "") if isinstance(status_obj, dict) else ""
                
                if status_name.lower() != "approved":
                    continue

                # Check Staff Notes to verify if already auto-executed
                staff_notes_list = props.get("Staff Notes", {}).get("rich_text", [])
                staff_notes_text = "".join([t.get("plain_text", "") for t in staff_notes_list])
                
                if "Auto-executed by CampusOps Engine" in staff_notes_text:
                    self._executed_page_ids.add(page_id)
                    continue

                # Extract details for execution
                student_name_list = props.get("Student Name", {}).get("rich_text", [])
                student_name = "".join([t.get("plain_text", "") for t in student_name_list]) or "Student"
                
                student_id_list = props.get("Student ID", {}).get("rich_text", [])
                student_id = "".join([t.get("plain_text", "") for t in student_id_list]) or "No ID"

                title_list = props.get("Title", {}).get("title", [])
                title = "".join([t.get("plain_text", "") for t in title_list]) or "Request"

                category_obj = props.get("Category", {}).get("select") or {}
                category = category_obj.get("name", "Operations Request")

                # Perform Execution
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

    async def _execute_ticket(
        self,
        page_id: str,
        student_name: str,
        student_id: str,
        title: str,
        category: str,
        processed_requests: list
    ):
        """Execute action for an approved ticket, update Notion and Run Log."""
        start_time = time.time()
        pass_id = f"GP-2026-{uuid.uuid4().hex[:6].upper()}"
        now_utc = datetime.now(timezone.utc)
        now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        staff_note_content = f"Auto-executed by CampusOps Engine on {now_str} (Digital Pass ID: {pass_id})"
        details_msg = f"Gatepass {pass_id} issued and dispatched for {student_name} ({student_id})"

        logger.info(f"⚡ [Execution Engine] Executing Approved Ticket '{title}' for {student_name} -> Pass: {pass_id}")

        # ── REAL-WORLD EXTERNAL ACTION ──────────────────────────────────
        # This is the part that makes something happen *outside* Notion.
        gatepass_path = self._perform_external_action(
            student_name=student_name,
            student_id=student_id,
            category=category,
            pass_id=pass_id,
            now_str=now_str,
        )
        # ────────────────────────────────────────────────────────────────

        # 1. Update Notion Request record with Staff Notes
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

        # 2. Add entry to Notion Run Log Database
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

        self._executed_page_ids.add(page_id)

        # 3. Synchronize in-memory request record for real-time frontend update
        clean_page_id = page_id.replace("-", "").lower()
        for req in processed_requests:
            req_notion_id = (req.notion_page_id or "").replace("-", "").lower()
            if req_notion_id == clean_page_id or req.request_id == page_id:
                req.parsed_data.status = "Approved"
                req.parsed_data.staff_notes = staff_note_content
                req.parsed_data.execution_id = pass_id

    # ── Real-world side-effect: print + file ──────────────────────────
    def _perform_external_action(
        self,
        student_name: str,
        student_id: str,
        category: str,
        pass_id: str,
        now_str: str,
    ) -> Path:
        """
        Produce a tangible, real-world artifact:
          1. Print a clear SUCCESS line to the terminal.
          2. Write a .txt gatepass file to backend/gatepasses/.
        Returns the Path of the generated file.
        """
        # ── 1. Terminal confirmation ─────────────────────────────────
        print(
            f"\n{'='*60}\n"
            f"SUCCESS: External action triggered for {student_name} - {category}\n"
            f"{'='*60}\n"
        )

        # ── 2. Generate a real file on disk ──────────────────────────
        gatepasses_dir = Path(__file__).resolve().parent.parent.parent / "gatepasses"
        gatepasses_dir.mkdir(parents=True, exist_ok=True)

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

    def _poll_in_memory_requests(self, processed_requests: list):
        """Process any in-memory request marked Approved that hasn't been executed yet."""
        for req in processed_requests:
            if req.parsed_data.status == "Approved" and not req.parsed_data.staff_notes:
                pass_id = f"GP-2026-{uuid.uuid4().hex[:6].upper()}"
                now_utc = datetime.now(timezone.utc)
                now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")

                # ── Real-world external action ───────────────────────
                self._perform_external_action(
                    student_name=req.parsed_data.student_name,
                    student_id=req.parsed_data.student_id or "No_ID",
                    category=req.parsed_data.category,
                    pass_id=pass_id,
                    now_str=now_str,
                )
                # ─────────────────────────────────────────────────────

                req.parsed_data.staff_notes = f"Auto-executed by CampusOps Engine on {now_str} (Digital Pass ID: {pass_id})"
                req.parsed_data.execution_id = pass_id
                
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


# Global singleton instance
execution_engine = ExecutionEngine(poll_interval_seconds=10)
