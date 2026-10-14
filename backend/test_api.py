import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api import app

def test_api():
    print("Testing FastAPI endpoints using TestClient...")
    client = TestClient(app)

    # 1. Health check
    print("Testing GET /api/health...")
    res = client.get("/api/health")
    print(f"Health Response Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    health_data = res.json()
    print("Health JSON:", health_data)
    assert health_data["status"] == "ok"

    # 2. Query endpoint
    print("\nTesting POST /api/query...")
    query_payload = {
        "question": "What is the resolution runbook for error ERR-409-TIMEOUT?",
        "use_reranker": True,
        "run_eval": False
    }
    res = client.post("/api/query", json=query_payload)
    print(f"Query Response Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    query_data = res.json()
    print(f"Answer: {query_data['answer'][:100]}...")
    print(f"Citations: {query_data['citations']}")
    print(f"Is Grounded: {query_data['is_grounded']}")
    print(f"Latency: {query_data['latency_ms']} ms")
    assert "answer" in query_data
    assert "citations" in query_data
    assert "is_grounded" in query_data

    # 3. Empty question validation check
    print("\nTesting 400 validation on empty question...")
    bad_res = client.post("/api/query", json={"question": "   "})
    assert bad_res.status_code == 400

    print("\nALL API ENDPOINTS TESTED AND VERIFIED SUCCESSFULLY (200 OK)!")

if __name__ == "__main__":
    test_api()
