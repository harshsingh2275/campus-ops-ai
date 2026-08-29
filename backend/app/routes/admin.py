"""
routes/admin.py — Admin Operations Endpoints
============================================

Endpoints restricted to users with the 'admin' role:

``GET /admin/requests``
    Queries Notion for all requests across the campus without filtering by email.
    Supports query parameters for category, priority, search, and limit.

``POST /admin/requests/{notion_page_id}/approve``
    Updates the Status of a specific Notion page to 'Approved' and triggers
    the execution engine to dispatch gatepasses.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..config import settings
from ..dependencies.auth import require_admin
from ..models.request import ParsedStudentRequest, SubmitResponse
from ..models.user import User
from ..routes.submit import _processed_requests
from ..services.engine import execution_engine
from ..services.notion_service import notion_service

logger = logging.getLogger("campus_ops.admin")

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


# ---------------------------------------------------------------------------
# GET /admin/requests
# ---------------------------------------------------------------------------

@router.get(
    "/requests",
    response_model=List[SubmitResponse],
    summary="Get All Campus Requests (Admin Only)",
    description=(
        "Retrieves all student requests across the entire campus from the Notion "
        "Requests database without filtering by student email. Requires admin role."
    ),
)
async def get_all_requests(
    category: Optional[str] = Query(None, description="Filter by request category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search across title, student, summary"),
    limit: int = Query(50, ge=1, le=100),
    current_admin: User = Depends(require_admin),
) -> List[SubmitResponse]:
    """Admin endpoint to fetch all campus requests."""
    logger.info(
        "Admin user id=%s (%s) fetching all campus requests.",
        current_admin.id,
        current_admin.email,
    )

    # 1. Query Notion database for all requests
    if settings.is_notion_configured and notion_service.client:
        notion_results = notion_service.query_all_requests(
            category=category,
            priority=priority,
            search=search,
            limit=limit,
        )
        if notion_results:
            return notion_results

    # 2. Fallback to in-memory store for all requests
    results = list(_processed_requests)
    if category and category != "All":
        results = [r for r in results if r.parsed_data.category.lower() == category.lower()]
    if priority and priority != "All":
        results = [r for r in results if r.parsed_data.priority.lower() == priority.lower()]
    if search:
        s = search.lower()
        results = [
            r for r in results
            if s in r.parsed_data.title.lower()
            or s in r.parsed_data.student_name.lower()
            or (r.parsed_data.student_id and s in r.parsed_data.student_id.lower())
            or (r.parsed_data.email and s in r.parsed_data.email.lower())
            or s in r.parsed_data.summary.lower()
            or (r.parsed_data.location and s in r.parsed_data.location.lower())
        ]
    return results[:limit]


# ---------------------------------------------------------------------------
# POST /admin/requests/{notion_page_id}/approve
# ---------------------------------------------------------------------------

@router.post(
    "/requests/{notion_page_id}/approve",
    response_model=SubmitResponse,
    summary="Approve Request in Notion (Admin Only)",
    description=(
        "Updates the status of a specific Notion request page to 'Approved' and "
        "triggers the automated execution engine. Requires admin role."
    ),
)
async def approve_notion_request(
    notion_page_id: str,
    current_admin: User = Depends(require_admin),
) -> SubmitResponse:
    """Approve a specific Notion request page and trigger execution engine."""
    logger.info(
        "Admin user id=%s (%s) approving request page '%s'",
        current_admin.id,
        current_admin.email,
        notion_page_id,
    )

    # 1. Update status in live Notion
    if settings.is_notion_configured and notion_service.client:
        try:
            notion_service.update_page_status(page_id=notion_page_id, status_name="Approved")
        except Exception as e:
            logger.error("Failed to update Notion page %s status: %s", notion_page_id, e)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed updating status in Notion: {e}",
            )

    # 2. Update status in in-memory list if present
    matching_req = next(
        (r for r in _processed_requests if r.notion_page_id == notion_page_id or r.request_id == notion_page_id),
        None,
    )
    if matching_req:
        matching_req.parsed_data.status = "Approved"

    # 3. Trigger execution engine poller
    await execution_engine.poll_and_execute()

    if matching_req:
        return matching_req

    # 4. If not in memory, build and return a response object
    return SubmitResponse(
        success=True,
        message=f"Request {notion_page_id} status updated to Approved.",
        request_id=f"notion_{notion_page_id.replace('-', '')[:8]}",
        parsed_data=ParsedStudentRequest(
            title="Approved Notion Request",
            student_name="Campus Student",
            category="Operations Request",
            priority="High",
            status="Approved",
            summary=f"Notion page {notion_page_id} approved by admin {current_admin.email}.",
            urgency="Normal",
            raw_text="Admin approval",
        ),
        notion_page_id=notion_page_id,
        notion_page_url=f"https://notion.so/{notion_page_id.replace('-', '')}",
        mode="live" if settings.is_notion_configured else "simulated",
    )
