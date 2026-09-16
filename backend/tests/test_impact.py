from tests.conftest import login, auth_headers
from app import models as m


def headers(client):
    return auth_headers(login(client, 'auditor', 'auditor123'))


def test_shared_evidence_traces_all_dependencies_without_mutation(client, db_session):
    doc = db_session.query(m.Document).filter_by(doc_type=m.DocumentType.GENERAL_LEDGER).first()
    before = [(a.id, a.status, a.updated_at) for a in db_session.query(m.Assertion).all()]
    events = db_session.query(m.AuditEvent).count()
    result = client.get(f'/impact/{doc.id}', headers=headers(client))
    assert result.status_code == 200
    report = result.json()
    assert report['affected_count'] == 20
    assert report['unaffected_count'] == 0
    assert len({r['id'] for r in report['assertions']}) == 20
    assert report['read_only'] is True
    db_session.expire_all()
    assert before == [(a.id, a.status, a.updated_at) for a in db_session.query(m.Assertion).all()]
    assert events == db_session.query(m.AuditEvent).count()


def test_invoice_preview_compares_ledger_and_preserves_conclusion(client, db_session):
    a = db_session.query(m.Assertion).filter_by(status='pass').first()
    ledger = db_session.query(m.LedgerEntry).filter_by(reference=a.subject_key).first()
    report = client.get(f'/impact/{a.primary_document_id}?proposed_amount={ledger.amount + 250}', headers=headers(client)).json()
    assert report['affected_count'] == 1
    assert report['unaffected_count'] == 19
    row = report['assertions'][0]
    assert row['comparison']['difference'] == 250
    assert row['comparison']['matches'] is False
    assert row['status'] == 'pass'
    assert row['relationship'] == 'primary source'


def test_prior_versions_and_approvals_are_visible(client, db_session):
    a = db_session.query(m.Assertion).filter_by(status='needs_review').first()
    old_id = a.primary_document_id
    reviewer = auth_headers(login(client, 'reviewer', 'reviewer123'))
    task = db_session.query(m.ReviewTask).filter_by(assertion_id=a.id).first()
    approved = client.post(f'/review/tasks/{task.id}/action', json={'decision':'approve','note':'Synthetic review'}, headers=reviewer)
    assert approved.status_code == 200
    amended = client.post(f'/documents/{old_id}/amend', json={'new_amount':12345}, headers=headers(client))
    assert amended.status_code == 200
    new_id = amended.json()['new_document_id']
    report = client.get(f'/impact/{new_id}', headers=headers(client)).json()
    assert report['affected_count'] == 1
    assert report['document']['prior_versions'] == 1
    assert report['assertions'][0]['source_version_stale'] is True
    assert report['approvals_to_revisit'] == 1
    assert client.get(f'/impact/{old_id}', headers=headers(client)).status_code == 409


def test_validation_and_auth(client, db_session):
    doc = db_session.query(m.Document).filter_by(doc_type=m.DocumentType.INVOICE).first()
    assert client.get(f'/impact/{doc.id}').status_code == 401
    auth = headers(client)
    assert client.get('/impact/missing', headers=auth).status_code == 404
    for amount in ['-1', 'NaN', 'inf', '1000000000001']:
        assert client.get(f'/impact/{doc.id}?proposed_amount={amount}', headers=auth).status_code == 422
    ledger = db_session.query(m.Document).filter_by(doc_type=m.DocumentType.GENERAL_LEDGER).first()
    assert client.get(f'/impact/{ledger.id}?proposed_amount=1', headers=auth).status_code == 422


def test_duplicate_links_do_not_double_count_and_other_engagement_is_excluded(client, db_session):
    doc = db_session.query(m.Document).filter_by(doc_type=m.DocumentType.INVOICE).first()
    a = db_session.query(m.Assertion).filter_by(primary_document_id=doc.id).first()
    db_session.add(m.EvidenceLink(assertion_id=a.id, document_id=doc.id, relation='supports'))
    other = m.Engagement(name='Other', client_name='Other', period_start='2025-01-01', period_end='2025-12-31')
    db_session.add(other)
    db_session.flush()
    cross = m.Assertion(engagement_id=other.id, label='Other', assertion_type='test', subject_key='other', confidence=1, primary_document_id=doc.id)
    db_session.add(cross)
    db_session.commit()
    report = client.get(f'/impact/{doc.id}', headers=headers(client)).json()
    assert report['affected_count'] == 1
    assert report['total_assertions'] == 20


def test_ambiguous_ledger_does_not_fabricate_comparison(client, db_session):
    a = db_session.query(m.Assertion).filter_by(status='pass').first()
    db_session.add(m.LedgerEntry(engagement_id=a.engagement_id, reference=a.subject_key, account='test', entry_date='2025-01-01', amount=1, currency='USD'))
    db_session.commit()
    report = client.get(f'/impact/{a.primary_document_id}?proposed_amount=1', headers=headers(client)).json()
    assert report['assertions'][0]['comparison'] is None
