import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.parser import RequestParser
from app.models.request import StudentRequestInput

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "notion" in data
    assert "http://localhost:3000" in data["cors"]["allowed_origins"]


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Campus Ops AI" in response.json()["message"]


def test_parser_lab_access():
    input_data = StudentRequestInput(
        raw_text="Hi, I need access to the Robotics Lab (Block B, Room 204) this Friday from 4 PM to 8 PM. My student ID is CS2024-042 and email is alex@campus.edu. Thanks, Alex Kumar"
    )
    parsed = RequestParser.parse(input_data)
    assert parsed.category == "Lab Access"
    assert parsed.student_id == "CS2024-042"
    assert parsed.email == "alex@campus.edu"
    assert "Robotics Lab" in (parsed.location or "") or "Block B" in (parsed.location or "")
    assert "Friday" in (parsed.date_needed or "")


def test_parser_maintenance_urgent():
    input_data = StudentRequestInput(
        raw_text="URGENT: AC is leaking water heavily in Hostel Block C Room 312. It might cause a short circuit! Please fix asap."
    )
    parsed = RequestParser.parse(input_data)
    assert parsed.category == "Maintenance & Repairs"
    assert parsed.priority in ["Urgent", "High"]
    assert "Block C" in (parsed.location or "") or "Room 312" in (parsed.location or "")


def test_parser_facility_booking():
    input_data = StudentRequestInput(
        raw_text="Requesting to book the Main Auditorium on 15th Sep from 10 AM to 2 PM for the annual cultural fest rehearsal."
    )
    parsed = RequestParser.parse(input_data)
    assert parsed.category in ["Facility Booking", "Event Approval"]
    assert "Auditorium" in (parsed.location or "")


def test_submit_route_end_to_end():
    payload = {
        "raw_text": "Need permission for after-hours workbench access in Hardware Lab Room 101 on Thursday 6pm-9pm. Student ID: EC-9948, Email: dev@college.edu.",
        "student_name": "Dev Patel",
        "source": "test_suite"
    }
    response = client.post("/api/submit", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "request_id" in data
    assert data["parsed_data"]["category"] == "Lab Access"
    assert data["parsed_data"]["student_id"] == "EC-9948"
    assert data["parsed_data"]["email"] == "dev@college.edu"
    assert data["notion_page_id"] is not None
    assert data["run_log_id"] is not None


def test_logs_endpoint():
    response = client.get("/api/logs?limit=5")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert "event_name" in logs[0]
