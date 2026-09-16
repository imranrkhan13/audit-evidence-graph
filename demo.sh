#!/usr/bin/env bash
# Scripted demo walkthrough for the Audit Evidence Graph + Tie-Out Workbench.
# Assumes the backend is running locally on :8000 (either via docker-compose
# or `uvicorn app.main:app` inside backend/ with the venv active) and has
# already been seeded.
set -euo pipefail
BASE="http://localhost:8000"

echo "== 1. Health check =="
curl -s "$BASE/health"; echo

echo "== 2. Login as auditor =="
TOKEN=$(curl -s -X POST "$BASE/auth/login" -d "username=auditor&password=auditor123" \
  -H "Content-Type: application/x-www-form-urlencoded" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
echo "token acquired"

ENG_ID=$(curl -s "$BASE/engagements" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['id'])")
echo "== 3. Engagement: $ENG_ID =="

echo "== 4. Dashboard =="
curl -s "$BASE/engagements/$ENG_ID/dashboard" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo "== 5. Review queue (sorted by financial impact) =="
curl -s "$BASE/review/queue?engagement_id=$ENG_ID&sort_by=financial_impact" -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo "== 6. Approve the first open review task (as reviewer) =="
RTOKEN=$(curl -s -X POST "$BASE/auth/login" -d "username=reviewer&password=reviewer123" \
  -H "Content-Type: application/x-www-form-urlencoded" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
TASK_ID=$(curl -s "$BASE/review/queue?engagement_id=$ENG_ID" -H "Authorization: Bearer $RTOKEN" | python3 -c "import sys,json;print(json.load(sys.stdin)[0]['id'])")
curl -s -X POST "$BASE/review/tasks/$TASK_ID/action" -H "Authorization: Bearer $RTOKEN" \
  -H "Content-Type: application/json" -d '{"decision":"approve","note":"Confirmed via scripted demo."}'; echo

echo "== 7. Export JSON (auditor-ready, evidence-linked) =="
curl -s "$BASE/export/$ENG_ID.json" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json;d=json.load(sys.stdin);print(f\"{len(d['assertions'])} assertions exported, each with linked evidence.\")"

echo "== 8. Continuous Risk Monitoring: risk radar (ranked, not sampled) =="
curl -s "$BASE/risk/radar?engagement_id=$ENG_ID" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
flags = json.load(sys.stdin)
print(f'{len(flags)} ledger entries flagged, highest risk first:')
for f in flags[:5]:
    codes = ', '.join(s['code'] for s in f['signals'])
    print(f\"  {f['reference']:14s} score={f['risk_score']:3d}  {codes}\")
"

echo "== 9. Evidence search (deterministic TF-IDF, locates evidence only) =="
curl -s "$BASE/evidence/search?engagement_id=$ENG_ID&query=Ferrostone%20Manufacturing%20invoice" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
results = json.load(sys.stdin)
print(f'Top {min(3,len(results))} matches:')
for r in results[:3]:
    print(f\"  {r['document_title']} (p.{r['page_number']}) score={r['score']}\")
"

echo "== Demo complete =="
