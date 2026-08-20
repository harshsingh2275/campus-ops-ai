import time
import os
import httpx
from notion_client import Client

NOTION_API_KEY = "dummy_token_for_github"

def test_external_action():
    base = "http://127.0.0.1:8000"

    print("\n=== 1. Submit a fresh request ===")
    r = httpx.post(f"{base}/api/submit", json={
        "raw_text": "Lab access needed for Robotics Lab on Wednesday 2pm-5pm for final year project testing. Student ID: ME2024-445.",
        "student_name": "Ankit Verma"
    }, timeout=15.0)
    assert r.status_code == 200
    data = r.json()
    page_id = data["notion_page_id"]
    print(f"  Notion Page: {page_id}")

    print("\n=== 2. Set status to Approved in Notion ===")
    client = Client(auth=NOTION_API_KEY)
    client.pages.update(page_id=page_id, properties={
        "Status": {"select": {"name": "Approved"}}
    })
    print("  Done.")

    print("\n=== 3. Waiting up to 25s for background poller ===")
    staff_notes = ""
    for i in range(12):
        time.sleep(2)
        page = client.pages.retrieve(page_id=page_id)
        notes = page["properties"].get("Staff Notes", {}).get("rich_text", [])
        staff_notes = "".join(t["plain_text"] for t in notes)
        if "Auto-executed" in staff_notes:
            print(f"  Detected after ~{(i+1)*2}s")
            break
    print(f"  Staff Notes: {staff_notes}")
    assert "Auto-executed by CampusOps Engine" in staff_notes, "Engine did NOT fire!"

    print("\n=== 4. Check gatepass file on disk ===")
    gatepasses_dir = os.path.join(os.path.dirname(__file__), "..", "gatepasses")
    gatepasses_dir = os.path.abspath(gatepasses_dir)
    target_file = os.path.join(gatepasses_dir, "Approved_Gatepass_ME2024-445.txt")
    assert os.path.isfile(target_file), f"File not found: {target_file}"
    contents = open(target_file, encoding="utf-8").read()
    print(f"  File exists: {target_file}")
    print(f"  Contents:\n{contents}")
    assert "This is an auto-generated gatepass for Ankit Verma." in contents

    print("\n=== 5. Check Run Log for Action Execution event ===")
    logs = httpx.get(f"{base}/api/logs?limit=5").json()
    action = next((l for l in logs if l["event_type"] == "Action Execution"), None)
    assert action, "No Action Execution log found!"
    print(f"  Event: {action['event_type']}")
    print(f"  Details: {action['details']}")

    print("\n" + "="*60)
    print("ALL EXTERNAL ACTION TESTS PASSED!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_external_action()
