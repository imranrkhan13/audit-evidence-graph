from tests.conftest import login, auth_headers
from app import models


def test_approve_review_task_is_atomic_and_creates_audit_event(client, db_session):
    token = login(client, "reviewer", "reviewer123")
    task = db_session.query(models.ReviewTask).filter(models.ReviewTask.status == "open").first()
    assertion_id = task.assertion_id

    resp = client.post(f"/review/tasks/{task.id}/action",
                        json={"decision": "approve", "note": "Confirmed with client controller."},
                        headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["new_status"] == "approved"
    assert body["assertion_status"] == "pass"

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_session.get_bind())
    fresh = Session()
    try:
        approval = fresh.query(models.Approval).filter(models.Approval.review_task_id == task.id).first()
        assert approval is not None
        assert approval.decision == "approve"

        events = fresh.query(models.AuditEvent).filter(
            models.AuditEvent.entity_id == assertion_id, models.AuditEvent.event_type == "approval"
        ).all()
        assert len(events) == 1

        refreshed_task = fresh.query(models.ReviewTask).filter(models.ReviewTask.id == task.id).first()
        assert refreshed_task.status == "approved"
    finally:
        fresh.close()


def test_cannot_act_twice_on_same_review_task(client, db_session):
    token = login(client, "reviewer", "reviewer123")
    task = db_session.query(models.ReviewTask).filter(models.ReviewTask.status == "open").first()
    r1 = client.post(f"/review/tasks/{task.id}/action", json={"decision": "reject"}, headers=auth_headers(token))
    assert r1.status_code == 200
    r2 = client.post(f"/review/tasks/{task.id}/action", json={"decision": "approve"}, headers=auth_headers(token))
    assert r2.status_code == 400


def test_review_queue_sortable_by_financial_impact(client):
    token = login(client, "auditor", "auditor123")
    engagements = client.get("/engagements", headers=auth_headers(token)).json()
    eng_id = engagements[0]["id"]
    resp = client.get("/review/queue", params={"engagement_id": eng_id, "sort_by": "financial_impact"},
                       headers=auth_headers(token))
    assert resp.status_code == 200
    rows = resp.json()
    impacts = [r["financial_impact"] for r in rows]
    assert impacts == sorted(impacts, reverse=True)


def test_audit_timeline_has_full_lifecycle_event_types(client, db_session):
    token = login(client, "admin", "admin123")
    eng = db_session.query(models.Engagement).first()
    resp = client.get("/audit-events", params={"engagement_id": eng.id}, headers=auth_headers(token))
    assert resp.status_code == 200
    event_types = {e["event_type"] for e in resp.json()}
    assert {"extraction", "normalization", "tie_out", "review"}.issubset(event_types)


def test_risk_radar_returns_ranked_flags(client, db_session):
    token = login(client, "auditor", "auditor123")
    eng = db_session.query(models.Engagement).first()
    resp = client.get("/risk/radar", params={"engagement_id": eng.id}, headers=auth_headers(token))
    assert resp.status_code == 200
    flags = resp.json()
    assert len(flags) > 0
    scores = [f["risk_score"] for f in flags]
    assert scores == sorted(scores, reverse=True)
    assert all("signals" in f and len(f["signals"]) > 0 for f in flags)


def test_evidence_search_finds_seeded_invoice(client, db_session):
    token = login(client, "auditor", "auditor123")
    eng = db_session.query(models.Engagement).first()
    resp = client.get("/evidence/search", params={"engagement_id": eng.id, "query": "Blue Harbor Supplies"},
                       headers=auth_headers(token))
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0
    assert any("invoice" in r["document_title"].lower() for r in results)
