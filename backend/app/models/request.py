from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class StudentRequestInput(BaseModel):
    """Input payload for student requests submission."""
    raw_text: str = Field(
        ...,
        description="Unstructured student request text (e.g., natural language request, email body, complaint, or permission query).",
        min_length=3,
        examples=["I need access to Robotics Lab (Block B, Room 204) this Friday from 3 PM to 6 PM. My Student ID is CS2024-102 and email is student@campus.edu."]
    )
    student_name: Optional[str] = Field(None, description="Optional student name override if already authenticated.")
    student_id: Optional[str] = Field(None, description="Optional student ID override.")
    email: Optional[str] = Field(None, description="Optional student email override.")
    source: Optional[str] = Field("web_portal", description="Source interface (e.g., web_portal, chatbot, email_bridge).")

class ParsedStudentRequest(BaseModel):
    """Structured data extracted from unstructured student request text."""
    title: str = Field(..., description="Generated summary title for the Notion page.")
    student_name: str = Field("Student", description="Extracted or default student name.")
    student_id: Optional[str] = Field(None, description="Extracted student identification code/roll number.")
    email: Optional[str] = Field(None, description="Extracted contact email.")
    category: str = Field(
        "General Inquiry",
        description="Categorized operational domain: 'Lab Access', 'Maintenance & Repairs', 'Facility Booking', 'Academic Request', 'IT & Equipment Support', 'Event Approval', 'General Inquiry'."
    )
    priority: str = Field("Medium", description="'Low', 'Medium', 'High', or 'Urgent'.")
    status: str = Field("Pending", description="'Pending', 'In Review', 'Approved', 'Rejected', or 'Completed'.")
    location: Optional[str] = Field(None, description="Identified room, hall, building, or lab location.")
    summary: str = Field(..., description="Concise synopsis of the student's request.")
    urgency: str = Field("Normal", description="'Normal', 'High', 'Urgent', 'Immediate'.")
    date_needed: Optional[str] = Field(None, description="Target execution or reservation date/time if specified.")
    staff_notes: Optional[str] = Field(None, description="Operational notes or execution tracking info.")
    execution_id: Optional[str] = Field(None, description="Generated Gatepass ID or execution tracking code.")
    raw_text: str = Field(..., description="Original raw request string.")
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional extracted key-value parameters.")
    created_at: datetime = Field(default_factory=utc_now)

class SubmitResponse(BaseModel):
    """API response model for POST /api/submit."""
    success: bool
    message: str
    request_id: str
    parsed_data: ParsedStudentRequest
    notion_page_id: Optional[str] = None
    notion_page_url: Optional[str] = None
    run_log_id: Optional[str] = None
    mode: str = Field("live", description="'live' if pushed to Notion API, 'simulated' if running in local/fallback mode.")
    timestamp: datetime = Field(default_factory=utc_now)
