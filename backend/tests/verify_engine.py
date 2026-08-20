import time
import json
import httpx
from notion_client import Client

NOTION_API_KEY = "dummy_token_for_github"
REQUESTS_DB_ID = "3c2bff8a0e078013a745cccb7aef8c9f"
RUN_LOG_DB_ID = "3c2bff8a0e0780a08333d1453d1a5825"

def test_engine_flow():
    base_url = "http://127.0.0.1:8000"
    
    print("\n--- 1. Submitting new student request ---")
    payload = {
        "raw_text": "Requesting auditorium booking for IEEE workshop on 20th Sept from 9am to 1pm. Student ID: CS2024-889.",
        "student_name": "Rohan Mehra"
    }
    r = httpx.post(f"{base_url}/api/submit", json=payload, timeout=15.0)
    assert r.status_code == 200, "Submit failed"
    data = r.json()
    req_id = data["request_id"]
    page_id = data["notion_page_id"]
    print(f"Request ID: {req_id}")
    print(f"Notion Page ID: {page_id}")
    print(f"Initial Status: {data['parsed_data']['status']}")

    print("\n--- 2. Setting status to 'Approved' in Notion directly ---")
    client = Client(auth=NOTION_API_KEY)
    client.pages.update(
        page_id=page_id,
        properties={
            "Status": {
                "select": {"name": "Approved"}
            }
        }
    )
    print("Status updated to 'Approved' in Notion.")

    print("\n--- 3. Waiting up to 20 seconds for Background Poller cycle ---")
    staff_notes = ""
    for i in range(10):
        time.sleep(2)
        updated_page = client.pages.retrieve(page_id=page_id)
        notes_list = updated_page.get("properties", {}).get("Staff Notes", {}).get("rich_text", [])
        staff_notes = "".join([t.get("plain_text", "") for t in notes_list])
        if "Auto-executed by CampusOps Engine" in staff_notes:
            print(f"Detected auto-execution after ~{(i+1)*2}s!")
            break

    print(f"Final Staff Notes in Notion: {staff_notes}")
    assert "Auto-executed by CampusOps Engine" in staff_notes, "Engine did not update Staff Notes!"
    assert "Digital Pass ID: GP-2026-" in staff_notes, "Pass ID not generated!"

    print("\n--- 4. Checking Notion Run Log for 'Action Execution' Event ---")
    logs_res = httpx.get(f"{base_url}/api/logs?limit=5")
    assert logs_res.status_code == 200
    recent_logs = logs_res.json()
    action_log = next((l for l in recent_logs if l["event_type"] == "Action Execution"), None)
    assert action_log is not None, "Action Execution event not found in logs!"
    print(f"Captured Action Execution Event:")
    print(f" - Event: {action_log['event_type']}")
    print(f" - Status: {action_log['status']}")
    print(f" - Details: {action_log['details']}")
    print(f" - Duration: {action_log['execution_time_ms']} ms")

    print("\n--- 5. Checking Requests Feed (Operations Dashboard endpoint) ---")
    req_res = httpx.get(f"{base_url}/api/requests")
    assert req_res.status_code == 200
    feed = req_res.json()
    matching = next((item for item in feed if item["request_id"] == req_id or item["notion_page_id"] == page_id), None)
    if matching:
        print(f"Feed Status: {matching['parsed_data']['status']}")
        print(f"Feed Staff Notes: {matching['parsed_data']['staff_notes']}")

    print("\n>>> ALL BACKGROUND POLLER & EXECUTION ENGINE TESTS PASSED! <<<")

if __name__ == "__main__":
    test_engine_flow()
