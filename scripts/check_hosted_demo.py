"""Exercise the hosted adapter against an isolated, disposable database."""
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["SECRET_KEY"] = "only-for-isolated-hosted-adapter-tests"

with tempfile.TemporaryDirectory(prefix="audit-hosted-test-") as scratch:
    tempfile.tempdir = scratch
    from api.index import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200
        assert client.get("/api/engagements").status_code == 401
        login = client.post("/api/auth/login", data={"username": "auditor", "password": "auditor123"})
        assert login.status_code == 200, login.text
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        projects = client.get("/api/engagements", headers=headers).json()
        project_id = projects[0]["id"]
        summary = client.get(f"/api/engagements/{project_id}/dashboard", headers=headers)
        assert summary.status_code == 200, summary.text
        assert summary.json()["total_assertions"] == 20
        docs = client.get(f"/api/impact/documents?engagement_id={project_id}", headers=headers)
        assert docs.status_code == 200, docs.text
        invoice = next(doc for doc in docs.json() if doc["doc_type"] == "invoice")
        preview = client.get(f"/api/impact/{invoice['id']}?proposed_amount=14000", headers=headers)
        assert preview.status_code == 200, preview.text
        report = client.get(f"/api/export/{project_id}.json", headers=headers)
        assert report.status_code == 200, report.text
    print("Hosted adapter: health, authentication, dashboard, documents, change preview, and export passed.")
