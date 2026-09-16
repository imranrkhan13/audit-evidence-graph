from collections import Counter
from app import models


def test_seeded_assertion_status_breakdown(db_session):
    assertions = db_session.query(models.Assertion).all()
    assert len(assertions) == 20
    counts = Counter(a.status for a in assertions)
    assert counts["pass"] == 14
    assert counts["needs_review"] == 3
    assert counts["fail"] == 3  # 2 mismatch + 1 missing evidence


def test_seed_is_idempotent_when_rerun(db_session):
    # Running seed a second time against the same engine should reset
    # cleanly and produce the exact same, reproducible counts — not
    # accumulate duplicate rows.
    from app import seed as seed_module
    seed_module.run_seed()
    assertions = db_session.query(models.Assertion).all()
    # db_session was opened before rerun; open a fresh session bound to same engine
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=db_session.get_bind())
    fresh = Session()
    try:
        assertions = fresh.query(models.Assertion).all()
        assert len(assertions) == 20
        counts = Counter(a.status for a in assertions)
        assert counts["pass"] == 14
        assert counts["needs_review"] == 3
        assert counts["fail"] == 3
    finally:
        fresh.close()


def test_review_tasks_have_expected_reasons(db_session):
    reasons = Counter(t.reason for t in db_session.query(models.ReviewTask).all())
    assert reasons["low_confidence"] == 3
    assert reasons["material_exception"] == 2
    assert reasons["missing_evidence"] == 1


def test_all_low_confidence_assertions_below_threshold(db_session):
    review_tasks = db_session.query(models.ReviewTask).filter(models.ReviewTask.reason == "low_confidence").all()
    for t in review_tasks:
        assertion = db_session.query(models.Assertion).filter(models.Assertion.id == t.assertion_id).first()
        assert assertion.confidence < 0.85
