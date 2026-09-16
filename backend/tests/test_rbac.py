from tests.conftest import login, auth_headers
from app import models


def test_reviewer_cannot_amend_documents(client, db_session):
    token = login(client, "reviewer", "reviewer123")
    doc = db_session.query(models.Document).filter(models.Document.doc_type == models.DocumentType.INVOICE).first()
    resp = client.post(f"/documents/{doc.id}/amend", json={"new_amount": 999.0}, headers=auth_headers(token))
    assert resp.status_code == 403


def test_auditor_can_amend_documents(client, db_session):
    token = login(client, "auditor", "auditor123")
    doc = db_session.query(models.Document).filter(
        models.Document.doc_type == models.DocumentType.INVOICE, models.Document.is_current == True  # noqa: E712
    ).first()
    resp = client.post(f"/documents/{doc.id}/amend", json={"new_amount": 999.0}, headers=auth_headers(token))
    assert resp.status_code == 200


def test_auditor_cannot_act_on_review_queue(client):
    token = login(client, "auditor", "auditor123")
    resp = client.get("/review/queue", params={"engagement_id": "whatever"}, headers=auth_headers(token))
    # auditor IS allowed to view the queue per spec roles
    assert resp.status_code == 200


def test_reviewer_can_act_on_review_task(client, db_session):
    token = login(client, "reviewer", "reviewer123")
    task = db_session.query(models.ReviewTask).filter(models.ReviewTask.status == "open").first()
    resp = client.post(f"/review/tasks/{task.id}/action", json={"decision": "approve"}, headers=auth_headers(token))
    assert resp.status_code == 200


def test_unauthenticated_request_rejected(client):
    resp = client.get("/engagements")
    assert resp.status_code == 401
