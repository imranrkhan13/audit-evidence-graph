from tests.conftest import login, auth_headers
from app import models


def test_amend_document_creates_new_version_and_preserves_old(client, db_session):
    token = login(client, "admin", "admin123")
    doc = db_session.query(models.Document).filter(
        models.Document.doc_type == models.DocumentType.INVOICE, models.Document.is_current == True  # noqa: E712
    ).first()
    old_version = doc.version
    old_id = doc.id

    resp = client.post(f"/documents/{old_id}/amend", json={"new_amount": 55555.55}, headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["new_version"] == old_version + 1

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_session.get_bind())
    fresh = Session()
    try:
        old_doc = fresh.query(models.Document).filter(models.Document.id == old_id).first()
        assert old_doc.is_current is False
        assert old_doc.superseded_by_id == body["new_document_id"]

        new_doc = fresh.query(models.Document).filter(models.Document.id == body["new_document_id"]).first()
        assert new_doc.is_current is True
        assert new_doc.content_hash != old_doc.content_hash
    finally:
        fresh.close()


def test_rerun_only_touches_affected_assertion_and_keeps_history(client, db_session):
    token = login(client, "admin", "admin123")
    all_assertions_before = {a.id: a.status for a in db_session.query(models.Assertion).all()}

    doc = db_session.query(models.Document).filter(
        models.Document.doc_type == models.DocumentType.INVOICE, models.Document.is_current == True  # noqa: E712
    ).first()
    resp = client.post(f"/documents/{doc.id}/amend", json={"new_amount": 1.23}, headers=auth_headers(token))
    assert resp.status_code == 200
    rerun_ids = {u["assertion_id"] for u in resp.json()["rerun_assertions"]}
    assert len(rerun_ids) == 1

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_session.get_bind())
    fresh = Session()
    try:
        for aid, old_status in all_assertions_before.items():
            a = fresh.query(models.Assertion).filter(models.Assertion.id == aid).first()
            if aid in rerun_ids:
                continue
            assert a.status == old_status, "rerun must not touch unrelated assertions"

        rerun_assertion_id = next(iter(rerun_ids))
        history = fresh.query(models.TieOutResult).filter(
            models.TieOutResult.assertion_id == rerun_assertion_id, models.TieOutResult.is_current == False  # noqa: E712
        ).all()
        assert len(history) > 0, "prior tie-out result must be preserved in history, not deleted"
    finally:
        fresh.close()


def test_export_json_links_every_assertion_to_evidence(client, db_session):
    token = login(client, "admin", "admin123")
    eng = db_session.query(models.Engagement).first()
    resp = client.get(f"/export/{eng.id}.json", headers=auth_headers(token))
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["export_type"] == "SYNTHETIC_DEMO_EXPORT"
    assert len(payload["assertions"]) == 20
    for row in payload["assertions"]:
        assert len(row["evidence"]) >= 1, f"assertion {row['assertion_id']} has no linked evidence"
        assert "rule_results" in row


def test_export_html_renders_and_mentions_synthetic_disclaimer(client, db_session):
    token = login(client, "admin", "admin123")
    eng = db_session.query(models.Engagement).first()
    resp = client.get(f"/export/{eng.id}.html", headers=auth_headers(token))
    assert resp.status_code == 200
    assert "synthetic" in resp.text.lower()


def test_content_hash_present_for_all_documents(db_session):
    docs = db_session.query(models.Document).all()
    for d in docs:
        assert d.content_hash and len(d.content_hash) == 64  # sha256 hex digest
