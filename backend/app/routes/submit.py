import time
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..config import settings
from ..models.request import StudentRequestInput, SubmitResponse
from ..models.run_log import RunLogEventType, RunLogStatus
from ..models.user import User
from ..services.parser import RequestParser
from ..services.notion_service import notion_service, log_submission_event
from ..dependencies.auth import get_current_user

logger = logging.getLogger("campus_ops.routes.submit")
router = APIRouter(prefix="/api", tags=["Student Requests"])

# In-memory storage for processed requests
_processed_requests: List[SubmitResponse] = []
MAX_SAVED_REQUESTS = 200


@router.post(
    "/submit",
    response_model=SubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit and parse unstructured student request",
    description="Accepts raw unstructured student requests, parses them into structured domain fields, and pushes a rich formatted page to the Notion Requests database while logging to the Notion Run Log."
)
async def submit_student_request(
    payload: StudentRequestInput,
    current_user: User = Depends(get_current_user),
):
    start_time = time.time()
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    logger.info(f"Received new student request [{request_id}] (len: {len(payload.raw_text)} chars)")

    try:
        # Step 1: Parse unstructured text into structured fields
        parsed_data = RequestParser.parse(payload)
        logger.info(f"[{request_id}] Parsed Category: '{parsed_data.category}', Priority: '{parsed_data.priority}', Location: '{parsed_data.location}'")

        # Step 2: Push to Notion Requests Database
        notion_result = notion_service.create_request_page(
            parsed_req=parsed_data,
            request_id=request_id
        )

        total_elapsed_ms = (time.time() - start_time) * 1000

        # Step 3: Log submission event to Notion Run Log
        log_entry = log_submission_event(
            event_type=RunLogEventType.REQUEST_INGESTION,
            status=RunLogStatus.SUCCESS,
            details=f"Processed request '{parsed_data.title}' for student '{parsed_data.student_name}' ({parsed_data.student_id or 'No ID'}). Category: {parsed_data.category}. Notion Page: {notion_result.get('page_id')}.",
            execution_time_ms=total_elapsed_ms,
            request_id=request_id,
            metadata={
                "category": parsed_data.category,
                "priority": parsed_data.priority,
                "urgency": parsed_data.urgency,
                "mode": notion_result.get("mode"),
                "notion_page_id": notion_result.get("page_id"),
                "source": payload.source
            }
        )

        response_obj = SubmitResponse(
            success=True,
            message="Student request parsed and pushed to Notion successfully.",
            request_id=request_id,
            parsed_data=parsed_data,
            notion_page_id=notion_result.get("page_id"),
            notion_page_url=notion_result.get("url"),
            run_log_id=log_entry.id,
            mode=notion_result.get("mode", "live")
        )

        # Store in circular buffer
        _processed_requests.insert(0, response_obj)
        if len(_processed_requests) > MAX_SAVED_REQUESTS:
            _processed_requests.pop()

        return response_obj

    except Exception as exc:
        total_elapsed_ms = (time.time() - start_time) * 1000
        error_msg = str(exc)
        logger.error(f"[{request_id}] Error processing student request: {error_msg}", exc_info=True)

        # Log Failure Event to Run Log
        log_submission_event(
            event_type=RunLogEventType.REQUEST_INGESTION,
            status=RunLogStatus.FAILURE,
            details=f"Failed processing student request [{request_id}]: {error_msg}",
            execution_time_ms=total_elapsed_ms,
            request_id=request_id,
            error_message=error_msg,
            metadata={"raw_text_length": len(payload.raw_text)}
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": f"Failed to process and sync student request: {error_msg}",
                "request_id": request_id
            }
        )


@router.get(
    "/requests",
    response_model=List[SubmitResponse],
    summary="Get List of Submitted Requests",
    description="Retrieves submitted requests stream with optional category, priority, or search query filtering."
)
async def get_requests(
    category: Optional[str] = Query(None, description="Filter by request category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search across title, student, summary"),
    limit: int = Query(50, ge=1, le=100)
):
    results = _processed_requests
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
            or s in r.parsed_data.summary.lower()
            or (r.parsed_data.location and s in r.parsed_data.location.lower())
        ]
    return results[:limit]


@router.post(
    "/requests/{request_id}/approve",
    response_model=SubmitResponse,
    summary="Approve Request & Trigger Engine Execution",
    description="Sets status to 'Approved' in Notion and triggers automated execution pass generation."
)
async def approve_request(request_id: str):
    # Find request in memory
    matching_req = next((r for r in _processed_requests if r.request_id == request_id or r.notion_page_id == request_id), None)
    
    if not matching_req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request {request_id} not found."
        )

    matching_req.parsed_data.status = "Approved"

    # If live Notion is configured, update Status in Notion
    if settings.is_notion_configured and matching_req.notion_page_id and notion_service.client:
        try:
            notion_service.client.pages.update(
                page_id=matching_req.notion_page_id,
                properties={
                    "Status": {
                        "select": {"name": "Approved"}
                    }
                }
            )
            logger.info(f"Updated Notion page {matching_req.notion_page_id} status to 'Approved'.")
        except Exception as e:
            logger.warning(f"Could not update Notion page status: {e}")

    # Trigger Execution Engine poll
    from ..services.engine import execution_engine
    await execution_engine.poll_and_execute()

    return matching_req
