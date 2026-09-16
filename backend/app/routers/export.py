from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.deps import get_current_user

router = APIRouter(prefix="/export", tags=["export"])


def _build_export_payload(db: Session, engagement_id: str) -> dict:
    eng = db.query(models.Engagement).filter(models.Engagement.id == engagement_id).first()
    if not eng:
        raise HTTPException(404, "Engagement not found")

    assertions = db.query(models.Assertion).filter(models.Assertion.engagement_id == engagement_id).all()
    rows = []
    for a in assertions:
        links = db.query(models.EvidenceLink).filter(models.EvidenceLink.assertion_id == a.id).all()
        link_out = []
        for l in links:
            doc = db.query(models.Document).filter(models.Document.id == l.document_id).first() if l.document_id else None
            link_out.append({
                "relation": l.relation,
                "document_title": doc.title if doc else None,
                "document_content_hash": doc.content_hash if doc else None,
                "page_number": l.page_number,
            })
        results = db.query(models.TieOutResult).filter(
            models.TieOutResult.assertion_id == a.id, models.TieOutResult.is_current == True  # noqa: E712
        ).all()
        review_task = db.query(models.ReviewTask).filter(models.ReviewTask.assertion_id == a.id).order_by(
            models.ReviewTask.created_at.desc()).first()
        reviewer_decision = None
        if review_task:
            approval = db.query(models.Approval).filter(models.Approval.review_task_id == review_task.id).order_by(
                models.Approval.created_at.desc()).first()
            if approval:
                reviewer = db.query(models.User).filter(models.User.id == approval.reviewer_id).first()
                reviewer_decision = {
                    "reviewer": reviewer.display_name if reviewer else approval.reviewer_id,
                    "decision": approval.decision,
                    "note": approval.note,
                    "decided_at": approval.created_at.isoformat(),
                }
        rows.append({
            "assertion_id": a.id,
            "label": a.label,
            "subject_key": a.subject_key,
            "extracted_value": a.extracted_value,
            "confidence": a.confidence,
            "final_status": a.status,
            "evidence": link_out,
            "rule_results": [
                {"rule": r.rule_name, "passed": r.passed, "detail": r.detail} for r in results
            ],
            "reviewer_decision": reviewer_decision,
        })

    return {
        "export_type": "SYNTHETIC_DEMO_EXPORT",
        "disclaimer": "All data in this export is synthetic fixture data generated for demonstration purposes only. "
                       "It does not represent a real client, a real accounting firm, or a live Modus integration.",
        "engagement": {
            "id": eng.id, "name": eng.name, "client_name": eng.client_name,
            "period_start": eng.period_start, "period_end": eng.period_end,
        },
        "generated_at": datetime.utcnow().isoformat(),
        "assertions": rows,
    }


@router.get("/{engagement_id}.json")
def export_json(engagement_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return _build_export_payload(db, engagement_id)


@router.get("/{engagement_id}.html")
def export_html(engagement_id: str, db: Session = Depends(get_db), _user=Depends(get_current_user)):
    payload = _build_export_payload(db, engagement_id)
    status_color = {"pass": "#1f7a4d", "needs_review": "#a8710a", "fail": "#a83232", "pending": "#666"}

    rows_html = ""
    for a in payload["assertions"]:
        color = status_color.get(a["final_status"], "#333")
        evidence_html = "".join(
            f"<li>{e['relation']}: {e['document_title'] or '(n/a)'} (page {e['page_number']}, "
            f"hash {e['document_content_hash'][:12] if e['document_content_hash'] else 'n/a'}...)</li>"
            for e in a["evidence"]
        )
        rules_html = "".join(
            f"<li>{'✅' if r['passed'] else '❌'} <b>{r['rule']}</b>: {r['detail']}</li>" for r in a["rule_results"]
        )
        reviewer_html = "No reviewer action recorded."
        if a["reviewer_decision"]:
            rd = a["reviewer_decision"]
            reviewer_html = f"{rd['decision']} by {rd['reviewer']} at {rd['decided_at']}" + (f" — \"{rd['note']}\"" if rd['note'] else "")
        rows_html += f"""
        <div style="border:1px solid #ddd; border-radius:4px; padding:12px; margin-bottom:12px;">
          <div style="display:flex; justify-content:space-between;">
            <strong>{a['label']}</strong>
            <span style="color:{color}; font-weight:bold; text-transform:uppercase;">{a['final_status']}</span>
          </div>
          <p>Extracted value: {a['extracted_value']} | Confidence: {a['confidence']:.2f}</p>
          <p><b>Evidence:</b></p><ul>{evidence_html}</ul>
          <p><b>Rule results:</b></p><ul>{rules_html}</ul>
          <p><b>Reviewer decision:</b> {reviewer_html}</p>
        </div>
        """

    html = f"""
    <html><head><meta charset="utf-8"><title>Audit Evidence Export</title></head>
    <body style="font-family: Georgia, serif; max-width: 900px; margin: 40px auto; color:#1a1a1a;">
      <h1>Audit Evidence & Tie-Out Export</h1>
      <p style="background:#fff3cd; border:1px solid #ffe08a; padding:10px; border-radius:4px;">
        {payload['disclaimer']}
      </p>
      <h2>{payload['engagement']['name']}</h2>
      <p>Client: {payload['engagement']['client_name']} | Period: {payload['engagement']['period_start']} to {payload['engagement']['period_end']}</p>
      <p>Generated at: {payload['generated_at']}</p>
      <h3>Assertions ({len(payload['assertions'])})</h3>
      {rows_html}
    </body></html>
    """
    return Response(content=html, media_type="text/html")
