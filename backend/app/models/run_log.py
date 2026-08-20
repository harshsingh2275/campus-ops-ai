from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class RunLogEventType(str, Enum):
    REQUEST_INGESTION = "Request Ingestion"
    REQUEST_PARSING = "Request Parsing"
    NOTION_SYNC = "Notion Sync"
    ACTION_EXECUTION = "Action Execution"
    SYSTEM_STARTUP = "System Startup"
    ERROR = "System Error"
    HEALTH_CHECK = "Health Check"

class RunLogStatus(str, Enum):
    SUCCESS = "Success"
    FAILURE = "Failure"
    WARNING = "Warning"
    IN_PROGRESS = "In Progress"

class RunLogCreate(BaseModel):
    """Payload to create a Run Log entry."""
    event_name: str = Field(..., description="Short descriptive title of the operation")
    event_type: RunLogEventType = Field(default=RunLogEventType.REQUEST_INGESTION)
    status: RunLogStatus = Field(default=RunLogStatus.SUCCESS)
    request_id: Optional[str] = Field(None, description="Correlated student request ID")
    execution_time_ms: float = Field(0.0, description="Duration in milliseconds")
    details: str = Field("", description="Detailed trace or description of the execution")
    error_message: Optional[str] = Field(None, description="Error message if status is FAILURE")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context payload")

class RunLogEntry(RunLogCreate):
    """Persisted Run Log Entry."""
    id: str = Field(..., description="Unique run log identifier")
    notion_page_id: Optional[str] = Field(None, description="Notion page ID if synced")
    created_at: datetime = Field(default_factory=utc_now)
