import os
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError

from ..config import settings
from ..models.request import ParsedStudentRequest
from ..models.run_log import RunLogCreate, RunLogEntry, RunLogEventType, RunLogStatus

logger = logging.getLogger("campus_ops.notion")
logging.basicConfig(level=logging.INFO)

# In-memory circular log buffer for fast diagnostics and frontend feed
_recent_run_logs: List[RunLogEntry] = []
MAX_RECENT_LOGS = 100


class NotionService:
    """Service wrapping official notion-client for Requests and Run Log database operations."""

    def __init__(self):
        self._client: Optional[Client] = None

    @property
    def client(self) -> Optional[Client]:
        if self._client is None and settings.NOTION_API_KEY:
            try:
                self._client = Client(auth=settings.NOTION_API_KEY)
                logger.info("Notion client initialized with live credentials.")
            except Exception as e:
                logger.error(f"Failed initializing Notion client: {e}")
                self._client = None
        return self._client

    def create_request_page(self, parsed_req: ParsedStudentRequest, request_id: str) -> Dict[str, Any]:
        """
        Pushes a structured student request page with rich content blocks
        to the Notion Requests Database.
        """
        start_time = time.time()
        
        # If Notion credentials are not configured, fallback to simulation
        if not settings.is_notion_configured or not self.client:
            simulated_page_id = f"sim-{uuid.uuid4().hex[:12]}"
            simulated_url = f"https://notion.so/campus-ops-requests/{simulated_page_id}"
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(f"[Simulated Notion] Request: {parsed_req.title} (ID: {simulated_page_id})")
            return {
                "page_id": simulated_page_id,
                "url": simulated_url,
                "mode": "simulated",
                "elapsed_ms": elapsed_ms
            }

        database_id = settings.NOTION_REQUESTS_DATABASE_ID

        # Schema matching user's 'CampusOps Requests' Notion Database
        # Properties: Title, Student Name, Student ID, Category, Priority, Status, AI Summary, Risk Flag
        is_risk = bool(parsed_req.priority in ["Urgent", "High"] or parsed_req.urgency == "Urgent")
        
        properties: Dict[str, Any] = {
            "Title": {
                "title": [{"text": {"content": parsed_req.title[:100]}}]
            },
            "Student Name": {
                "rich_text": [{"text": {"content": parsed_req.student_name}}]
            },
            "Category": {
                "select": {"name": parsed_req.category}
            },
            "Priority": {
                "select": {"name": parsed_req.priority}
            },
            "Status": {
                "select": {"name": "Pending Review" if parsed_req.status == "Pending" else parsed_req.status}
            },
            "AI Summary": {
                "rich_text": [{"text": {"content": parsed_req.summary[:1900]}}]
            },
            "Risk Flag": {
                "checkbox": is_risk
            }
        }

        if parsed_req.student_id:
            properties["Student ID"] = {
                "rich_text": [{"text": {"content": parsed_req.student_id}}]
            }

        # Rich Page Content Blocks
        children_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Campus Ops AI - Ingested Request"}}]
                }
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"Summary: {parsed_req.summary}\nPriority: {parsed_req.priority} | Urgency: {parsed_req.urgency}"}}
                    ],
                    "icon": {"emoji": "📋"}
                }
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "Key Extracted Entities"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": f"Student: {parsed_req.student_name} ({parsed_req.student_id or 'No ID'})"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": f"Category: {parsed_req.category} | Location: {parsed_req.location or 'Unspecified'}"}}]
                }
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [{"type": "text", "text": {"content": f"Schedule / Needed: {parsed_req.date_needed or 'Immediate / Not Specified'}"}}]
                }
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": "Raw Student Input"}}]
                }
            },
            {
                "object": "block",
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": parsed_req.raw_text}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"Request ID: {request_id} | Ingestion Timestamp: {datetime.now(timezone.utc).isoformat()}"}}
                    ]
                }
            }
        ]

        try:
            response = self.client.pages.create(
                parent={"database_id": database_id},
                properties=properties,
                children=children_blocks
            )
            elapsed_ms = (time.time() - start_time) * 1000
            page_id = response.get("id", "")
            page_url = response.get("url", f"https://notion.so/{page_id.replace('-', '')}")
            
            logger.info(f"Successfully pushed Live Page to Notion Requests DB! Page ID: {page_id} ({elapsed_ms:.1f}ms)")
            return {
                "page_id": page_id,
                "url": page_url,
                "mode": "live",
                "elapsed_ms": elapsed_ms
            }

        except APIResponseError as e:
            logger.warning(f"Notion Requests push warning ({e.code}): {e.message}. Retrying with minimal title...")
            try:
                fallback_props = {
                    "Title": {"title": [{"text": {"content": parsed_req.title[:100]}}]}
                }
                response = self.client.pages.create(
                    parent={"database_id": database_id},
                    properties=fallback_props,
                    children=children_blocks
                )
                elapsed_ms = (time.time() - start_time) * 1000
                page_id = response.get("id", "")
                page_url = response.get("url", f"https://notion.so/{page_id.replace('-', '')}")
                return {
                    "page_id": page_id,
                    "url": page_url,
                    "mode": "live_fallback",
                    "elapsed_ms": elapsed_ms
                }
            except Exception as retry_err:
                logger.error(f"Notion Requests create page failed: {retry_err}")
                raise e


    def log_run_event(
        self,
        event_type: RunLogEventType,
        status: RunLogStatus,
        details: str,
        execution_time_ms: float,
        request_id: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RunLogEntry:
        """
        Helper function to log execution/submission events to the Notion Run Log database
        and in-memory buffer.
        """
        log_id = f"log_{uuid.uuid4().hex[:10]}"
        event_name = f"[{event_type.value}] {status.value} - {request_id or 'sys'}"
        
        entry = RunLogEntry(
            id=log_id,
            event_name=event_name,
            event_type=event_type,
            status=status,
            request_id=request_id,
            execution_time_ms=execution_time_ms,
            details=details,
            error_message=error_message,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc)
        )

        # Store in in-memory buffer for instant UI feed
        _recent_run_logs.insert(0, entry)
        if len(_recent_run_logs) > MAX_RECENT_LOGS:
            _recent_run_logs.pop()

        # Push to Live Notion Run Log Database
        # Schema: Run (title), Event (select), Status (select), Timestamp (date), Request ID (rich_text), Details (rich_text)
        if settings.is_notion_configured and settings.NOTION_RUN_LOG_DATABASE_ID and self.client:
            try:
                log_properties: Dict[str, Any] = {
                    "Run": {
                        "title": [{"text": {"content": event_name[:100]}}]
                    },
                    "Event": {
                        "select": {"name": event_type.value}
                    },
                    "Status": {
                        "select": {"name": status.value}
                    },
                    "Timestamp": {
                        "date": {"start": datetime.now(timezone.utc).isoformat()}
                    },
                    "Details": {
                        "rich_text": [{"text": {"content": details[:1900]}}]
                    }
                }
                
                if request_id:
                    log_properties["Request ID"] = {
                        "rich_text": [{"text": {"content": request_id}}]
                    }

                notion_log = self.client.pages.create(
                    parent={"database_id": settings.NOTION_RUN_LOG_DATABASE_ID},
                    properties=log_properties
                )
                entry.notion_page_id = notion_log.get("id")
                logger.info(f"Successfully pushed entry to Notion Run Log DB: {entry.notion_page_id}")
            except Exception as e:
                logger.warning(f"Could not push Run Log to Notion: {e}")

        return entry

    def get_recent_logs(self, limit: int = 50) -> List[RunLogEntry]:
        """Return recent in-memory run logs."""
        return _recent_run_logs[:limit]


# Global singleton instance
notion_service = NotionService()


def log_submission_event(
    event_type: RunLogEventType,
    status: RunLogStatus,
    details: str,
    execution_time_ms: float,
    request_id: Optional[str] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> RunLogEntry:
    """Convenience helper function to log submission events."""
    return notion_service.log_run_event(
        event_type=event_type,
        status=status,
        details=details,
        execution_time_ms=execution_time_ms,
        request_id=request_id,
        error_message=error_message,
        metadata=metadata
    )
