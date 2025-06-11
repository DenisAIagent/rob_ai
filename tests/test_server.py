from fastapi.testclient import TestClient
from api import server
from api.server import app
from api.utils import Job, jobs
import uuid
from unittest.mock import patch

client = TestClient(app)

def test_analyze():
    resp = client.post("/api/analyze", json={"description": "A chat application"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["project_type"] == "realtime-chat"

async def dummy_start_generation(project_name: str, description: str) -> Job:
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, process=None, log_file="/tmp/dummy.log", status="completed", zip_path="/tmp/dummy.zip")
    jobs[job_id] = job
    return job

def test_generate_and_status():
    with patch("api.server.start_generation", dummy_start_generation):
        resp = client.post("/api/generate", json={"project_name": "test", "description": "desc"})
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]
        resp = client.get(f"/api/status/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

def test_analytics():
    server.analytics["projects_created"] = 0
    server.analytics["types"].clear()
    with patch("api.server.start_generation", dummy_start_generation):
        resp = client.post("/api/generate", json={"project_name": "a", "description": "chat app"})
        assert resp.status_code == 200
    resp = client.get("/api/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["projects_created"] == 1
    assert data["types"]["realtime-chat"] == 1
