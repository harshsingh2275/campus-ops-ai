import os
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError

from ..config import settings
from ..models.request import ParsedStudentRequest, SubmitResponse
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

        if parsed_req.email:
            properties["Student Email"] = {
                "email": parsed_req.email
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

    def query_requests_by_email(
        self,
        email: str,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[SubmitResponse]:
        """
        Query the Notion Requests database filtering by Student Email property.
        """
        if not settings.is_notion_configured or not self.client:
            return []

        try:
            # 1. Retrieve data_source_id or fallback to database_id
            db_id = settings.NOTION_REQUESTS_DATABASE_ID
            data_source_id = db_id
            try:
                db_info = self.client.databases.retrieve(database_id=db_id)
                data_sources = db_info.get("data_sources", [])
                if data_sources and isinstance(data_sources, list) and "id" in data_sources[0]:
                    data_source_id = data_sources[0]["id"]
            except Exception as e:
                logger.warning(f"Could not retrieve database info, using database_id as fallback: {e}")

            # 2. Build Notion query filter payload targeting Student Email
            filter_payload: Dict[str, Any] = {
                "property": "Student Email",
                "email": {
                    "equals": email
                }
            }

            # 3. Query Notion
            response = self.client.data_sources.query(
                data_source_id=data_source_id,
                filter=filter_payload
            )
            results = response.get("results", [])
            logger.info(f"Notion query for Student Email '{email}' returned {len(results)} records.")

            # 4. Transform Notion pages to SubmitResponse models
            responses: List[SubmitResponse] = []
            for page in results:
                props = page.get("properties", {})
                page_id = page.get("id", "")
                page_url = page.get("url", f"https://notion.so/{page_id.replace('-', '')}")

                title_list = props.get("Title", {}).get("title", [])
                title = "".join([t.get("plain_text", "") for t in title_list]) or "Request"

                student_name_list = props.get("Student Name", {}).get("rich_text", [])
                student_name = "".join([t.get("plain_text", "") for t in student_name_list]) or "Student"

                student_id_list = props.get("Student ID", {}).get("rich_text", [])
                student_id = "".join([t.get("plain_text", "") for t in student_id_list]) or None

                student_email_prop = props.get("Student Email", {})
                if student_email_prop.get("type") == "email" or "email" in student_email_prop:
                    student_email = student_email_prop.get("email") or email
                else:
                    email_list = student_email_prop.get("rich_text", [])
                    student_email = "".join([t.get("plain_text", "") for t in email_list]) or email

                category_obj = props.get("Category", {}).get("select") or {}
                req_category = category_obj.get("name", "General Inquiry")

                priority_obj = props.get("Priority", {}).get("select") or {}
                req_priority = priority_obj.get("name", "Medium")

                status_obj = props.get("Status", {}).get("select") or props.get("Status", {}).get("status") or {}
                req_status = status_obj.get("name", "Pending")

                summary_list = props.get("AI Summary", {}).get("rich_text", [])
                req_summary = "".join([t.get("plain_text", "") for t in summary_list]) or title

                risk_flag = props.get("Risk Flag", {}).get("checkbox", False)

                staff_notes_list = props.get("Staff Notes", {}).get("rich_text", [])
                staff_notes = "".join([t.get("plain_text", "") for t in staff_notes_list]) or None

                created_time_str = page.get("created_time")
                created_at = datetime.now(timezone.utc)
                if created_time_str:
                    try:
                        created_at = datetime.fromisoformat(created_time_str.replace("Z", "+00:00"))
                    except Exception:
                        pass

                # Apply optional in-memory filters
                if category and category != "All" and req_category.lower() != category.lower():
                    continue
                if priority and priority != "All" and req_priority.lower() != priority.lower():
                    continue
                if search:
                    s = search.lower()
                    if not (
                        s in title.lower()
                        or s in student_name.lower()
                        or (student_id and s in student_id.lower())
                        or s in req_summary.lower()
                    ):
                        continue

                parsed_req = ParsedStudentRequest(
                    title=title,
                    student_name=student_name,
                    student_id=student_id,
                    email=student_email,
                    category=req_category,
                    priority=req_priority,
                    status=req_status,
                    summary=req_summary,
                    urgency="Urgent" if risk_flag else "Normal",
                    staff_notes=staff_notes,
                    raw_text=req_summary,
                    created_at=created_at,
                )

                submit_resp = SubmitResponse(
                    success=True,
                    message="Fetched from Notion Requests Database",
                    request_id=f"notion_{page_id.replace('-', '')[:8]}",
                    parsed_data=parsed_req,
                    notion_page_id=page_id,
                    notion_page_url=page_url,
                    mode="live",
                    timestamp=created_at
                )
                responses.append(submit_resp)

            return responses[:limit]

        except Exception as exc:
            logger.error(f"Failed querying Notion requests by email: {exc}", exc_info=True)
            return []

    def query_all_requests(
        self,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> List[SubmitResponse]:
        """
        Query the Notion Requests database for all requests across the campus (Admin view).
        Does NOT filter by email.
        """
        if not settings.is_notion_configured or not self.client:
            return []

        try:
            db_id = settings.NOTION_REQUESTS_DATABASE_ID
            data_source_id = db_id
            try:
                db_info = self.client.databases.retrieve(database_id=db_id)
                data_sources = db_info.get("data_sources", [])
                if data_sources and isinstance(data_sources, list) and "id" in data_sources[0]:
                    data_source_id = data_sources[0]["id"]
            except Exception as e:
                logger.warning(f"Could not retrieve database info, using database_id as fallback: {e}")

            # Query all records without email filter
            response = self.client.data_sources.query(
                data_source_id=data_source_id
            )
            results = response.get("results", [])
            logger.info(f"Admin query for all campus requests returned {len(results)} records.")

            responses: List[SubmitResponse] = []
            for page in results:
                props = page.get("properties", {})
                page_id = page.get("id", "")
                page_url = page.get("url", f"https://notion.so/{page_id.replace('-', '')}")

                title_list = props.get("Title", {}).get("title", [])
                title = "".join([t.get("plain_text", "") for t in title_list]) or "Request"

                student_name_list = props.get("Student Name", {}).get("rich_text", [])
                student_name = "".join([t.get("plain_text", "") for t in student_name_list]) or "Student"

                student_id_list = props.get("Student ID", {}).get("rich_text", [])
                student_id = "".join([t.get("plain_text", "") for t in student_id_list]) or None

                student_email_prop = props.get("Student Email", {})
                if student_email_prop.get("type") == "email" or "email" in student_email_prop:
                    student_email = student_email_prop.get("email")
                else:
                    email_list = student_email_prop.get("rich_text", [])
                    student_email = "".join([t.get("plain_text", "") for t in email_list]) or None

                category_obj = props.get("Category", {}).get("select") or {}
                req_category = category_obj.get("name", "General Inquiry")

                priority_obj = props.get("Priority", {}).get("select") or {}
                req_priority = priority_obj.get("name", "Medium")

                status_obj = props.get("Status", {}).get("select") or props.get("Status", {}).get("status") or {}
                req_status = status_obj.get("name", "Pending")

                summary_list = props.get("AI Summary", {}).get("rich_text", [])
                req_summary = "".join([t.get("plain_text", "") for t in summary_list]) or title

                risk_flag = props.get("Risk Flag", {}).get("checkbox", False)

                staff_notes_list = props.get("Staff Notes", {}).get("rich_text", [])
                staff_notes = "".join([t.get("plain_text", "") for t in staff_notes_list]) or None

                created_time_str = page.get("created_time")
                created_at = datetime.now(timezone.utc)
                if created_time_str:
                    try:
                        created_at = datetime.fromisoformat(created_time_str.replace("Z", "+00:00"))
                    except Exception:
                        pass

                # Apply optional in-memory filters
                if category and category != "All" and req_category.lower() != category.lower():
                    continue
                if priority and priority != "All" and req_priority.lower() != priority.lower():
                    continue
                if search:
                    s = search.lower()
                    if not (
                        s in title.lower()
                        or s in student_name.lower()
                        or (student_id and s in student_id.lower())
                        or (student_email and s in student_email.lower())
                        or s in req_summary.lower()
                    ):
                        continue

                parsed_req = ParsedStudentRequest(
                    title=title,
                    student_name=student_name,
                    student_id=student_id,
                    email=student_email,
                    category=req_category,
                    priority=req_priority,
                    status=req_status,
                    summary=req_summary,
                    urgency="Urgent" if risk_flag else "Normal",
                    staff_notes=staff_notes,
                    raw_text=req_summary,
                    created_at=created_at,
                )

                submit_resp = SubmitResponse(
                    success=True,
                    message="Fetched from Notion Requests Database (Admin)",
                    request_id=f"notion_{page_id.replace('-', '')[:8]}",
                    parsed_data=parsed_req,
                    notion_page_id=page_id,
                    notion_page_url=page_url,
                    mode="live",
                    timestamp=created_at
                )
                responses.append(submit_resp)

            return responses[:limit]

        except Exception as exc:
            logger.error(f"Failed querying all Notion requests for admin: {exc}", exc_info=True)
            return []

    def update_page_status(self, page_id: str, status_name: str = "Approved") -> Dict[str, Any]:
        """
        Update the Status property of a Notion page.
        """
        if not settings.is_notion_configured or not self.client:
            return {"page_id": page_id, "status": status_name, "mode": "simulated"}

        try:
            res = self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "select": {"name": status_name}
                    }
                }
            )
            logger.info(f"Updated Notion page '{page_id}' Status to '{status_name}'")
            return res
        except Exception as e:
            logger.warning(f"Could not update Notion page status for '{page_id}': {e}")
            raise e


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
