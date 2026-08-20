import httpx
import json

def verify_live_backend():
    base_url = "http://127.0.0.1:8000"
    
    print("=== Pinging GET /api/health ===")
    r = httpx.get(f"{base_url}/api/health")
    print(f"Status Code: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    assert r.status_code == 200, "Health check failed"

    print("\n=== Testing POST /api/submit (Lab Access) ===")
    payload = {
        "raw_text": "Hi team, I urgently need permission to access the Robotics Lab (Block B, Room 204) this Friday from 4 PM to 8 PM for our IEEE hardware project. My student ID is CS2024-042 and email is alex@campus.edu. Thanks!",
        "student_name": "Alex Kumar"
    }
    r = httpx.post(f"{base_url}/api/submit", json=payload)
    print(f"Status Code: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    assert r.status_code == 200, "Submit request failed"
    res = r.json()
    assert res["success"] is True
    assert res["parsed_data"]["category"] == "Lab Access"
    assert res["parsed_data"]["student_id"] == "CS2024-042"
    assert res["parsed_data"]["email"] == "alex@campus.edu"

    print("\n=== Testing POST /api/submit (Maintenance Request) ===")
    payload2 = {
        "raw_text": "URGENT: Water leaking from AC unit in Hostel Block C Room 312 since morning. Please send maintenance urgently! Student ID: ME2023-881."
    }
    r2 = httpx.post(f"{base_url}/api/submit", json=payload2)
    print(f"Status Code: {r2.status_code}")
    print(json.dumps(r2.json(), indent=2))
    assert r2.status_code == 200
    res2 = r2.json()
    assert res2["parsed_data"]["category"] == "Maintenance & Repairs"
    assert res2["parsed_data"]["priority"] in ["Urgent", "High"]

    print("\n=== Testing CORS Preflight (OPTIONS /api/submit) ===")
    r_cors = httpx.options(
        f"{base_url}/api/submit",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    print(f"CORS Status: {r_cors.status_code}")
    print(f"CORS Allow Origin Header: {r_cors.headers.get('access-control-allow-origin')}")
    assert r_cors.headers.get("access-control-allow-origin") == "http://localhost:3000"

    print("\n=== Testing GET /api/logs ===")
    r_logs = httpx.get(f"{base_url}/api/logs?limit=5")
    print(f"Logs Status: {r_logs.status_code}")
    print(f"Recorded Logs count: {len(r_logs.json())}")
    for log in r_logs.json()[:3]:
        print(f" - [{log['event_type']}] {log['event_name']} ({log['execution_time_ms']}ms)")

    print("\n>>> ALL LIVE CHECKS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    verify_live_backend()
