# Build Status

Last updated: end of build session, all milestones below.

**Addendum:** a Continuous Risk Monitoring + Evidence Search feature was
added after researching Modus's public statements about their own product
(see README's "Feature addition" section for the sources and reasoning).

## Milestone status

| # | Milestone | Status |
|---|-----------|--------|
| 1 | Structure, schema, DB, seed data, auth/RBAC | ✅ Done |
| 2 | Ingestion, versions, pages, hashes | ✅ Done |
| 3 | Extraction, normalization, linking, confidence | ✅ Done |
| 4 | Tie-out engine, tolerances, failures, reruns | ✅ Done |
| 5 | Review queue, approvals, permissions, audit history | ✅ Done |
| 6 | Dashboard, evidence viewer, detail, export | ✅ Done |
| 7 | Tests, Docker, README, demo, final status | ✅ Done (Docker Compose written but not executed — see Limitations) |

## What's implemented

**Backend**
- 13-table SQLAlchemy data model + `users` table for auth.
- JWT auth, bcrypt password hashing, role dependency (`require_roles`)
  enforcing Admin / Auditor / Reviewer permissions per endpoint.
- Fixture extraction provider behind an `ExtractionProvider` ABC.
- Pure-function normalization module (invoice id, vendor, currency, amount,
  date, fixed-table currency conversion).
- Deterministic tie-out rule engine: invoice=ledger, line items=total, bank
  txn supports payment, payment date in period, identities match, duplicate
  invoice detection, missing evidence, explicit currency conversion,
  extraction-must-not-have-failed.
- Orchestration layer (`engine.py`) that runs all applicable rules per
  assertion, persists `TieOutResult` rows (marking prior ones
  `is_current=False` rather than deleting them), sets the assertion's final
  status, opens `ReviewTask` rows, and writes `AuditEvent` rows — used
  identically by the initial seed run and by reruns.
- Seed script producing exactly 20 assertions: 14 pass, 3 need review
  (confidence 0.58/0.72/0.80, all below 0.85), 2 fail on invoice/ledger
  mismatch (+$250.00 / -$75.50), 1 fails on missing evidence. Verified live.
- Document amendment endpoint (`POST /documents/{id}/amend`, Admin/Auditor
  only): creates a new version, marks the old one superseded (never
  deleted), and reruns **only** the assertion(s) tied to that invoice,
  preserving the prior tie-out result in history. Verified via test that
  unrelated assertions' statuses are untouched.
- Review queue with sort by financial impact / confidence / risk / status,
  and atomic approve / reject / request-evidence actions (approval row +
  status change + audit event all committed in one transaction or none).
- Append-only audit event log across ingestion, extraction, normalization,
  tie-out, review, approval, and export.
- JSON export (every assertion carries its evidence links, rule results,
  and reviewer decision) and a printable HTML export with an explicit
  synthetic-data disclaimer banner.

**Frontend**
- Vite + React + TypeScript + Tailwind, typed API client, JWT stored
  client-side, route guard redirecting unauthenticated users to `/login`.
- Design system applied per spec: stone background, navy typography, slate
  panel surfaces, thin borders, green/amber/red status badges, persistent
  left sidebar, compact top bar, no gradients/neon/decorative illustration.
- Pages, all wired to real backend data (no mock/static data anywhere):
  Login, Dashboard (engagement status, assertion counts, exception value,
  missing evidence, processing state), Assertions list, Assertion Detail
  (extracted value, confidence, quote, source doc/page link, evidence
  panel, linked ledger rows, tie-out rule results + history, reviewer
  decision), Review Queue (sortable, approve/reject/request-evidence with
  a note field), Document Viewer (page navigation, version, content hash),
  Audit Timeline (full event list), Evidence Export (JSON + HTML links).

## Test results

Backend: **48 / 48 passing** (`cd backend && python -m pytest -q`)
- `test_normalization.py` — 7 tests
- `test_tie_out.py` — 10 tests
- `test_seed_breakdown.py` — 4 tests (including seed idempotency)
- `test_rbac.py` — 5 tests
- `test_review_and_audit.py` — 4 tests (atomic approval + audit event,
  double-action rejection, sortable queue, audit timeline coverage)
- `test_versioning_and_export.py` — 5 tests (new version created, history
  preserved, rerun scoped to one assertion, export traceability, content
  hash presence)
- `test_anomaly.py` — 7 tests (deterministic risk scoring: outliers, round
  numbers, near-threshold, weekend postings, first-time vendors, sort order)
- `test_search.py` — 4 tests (TF-IDF ranking correctness, empty/no-match
  queries, and a structural test that the search module has no dependency
  on the data model or tie-out engine)
- 2 additional API tests in `test_review_and_audit.py` for `/risk/radar`
  and `/evidence/search`

Frontend:
- `npx tsc -b` — passes, no type errors.
- `npm run build` — production build succeeds (`dist/` ~190KB JS gzip'd to
  ~60KB).

End-to-end (manual, live server, not part of the automated suite):
- Started the backend against a freshly seeded SQLite DB, then via curl:
  confirmed `/health`, logged in as admin, listed engagements, pulled the
  dashboard (`total_assertions: 20, passed: 14, needs_review: 3, failed: 3,
  exception_value: 53765.0, missing_evidence_count: 1`), pulled the review
  queue (6 open tasks, sorted by financial impact), and exported JSON
  (20 assertions, each with evidence).
- Ran `demo.sh` end-to-end against the same live server: health → login →
  dashboard → review queue → approve one task → export. All steps
  succeeded and the approved task's assertion flipped to `pass`.

## Known limitations (see README for full list)

- Fixture extraction only — no real LLM/OCR call anywhere in this system.
- No vector/semantic search implemented (optional per spec; time was spent
  on the deterministic engine, RBAC, and test coverage instead).
- Fixed synthetic FX table, not a live rate feed.
- Document viewer shows extracted plain text, not real PDF rendering.
- `docker compose up` was written but **not executed** — no Docker daemon
  was available in the build environment. Backend and frontend were each
  verified independently outside Docker instead (pytest suite + live
  uvicorn smoke test for the backend; `tsc -b` + `vite build` for the
  frontend).
- The seeded 20-assertion scenario intentionally covers only the two
  exception categories named in the brief (mismatch, missing evidence);
  duplicate-invoice and identity-mismatch rules exist and are unit-tested
  but aren't triggered by the seeded data itself.

## Commands reference

```bash
# Backend tests
cd backend && python -m pytest -q

# Backend dev server (SQLite)
cd backend && DATABASE_URL=sqlite:///./audit_demo.db python -c "from app.seed import run_seed; run_seed()"
cd backend && DATABASE_URL=sqlite:///./audit_demo.db uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev     # dev server, proxies /api
cd frontend && npx tsc -b && npm run build    # type-check + production build

# Full stack via Docker Compose (not executed in this environment — see above)
docker compose up --build

# Scripted demo (requires a running, seeded backend on :8000)
./demo.sh
```

## September 15, 2026 — Evidence Change Impact and landing page

- Research matrix and product hypothesis documented in `RESEARCH.md`; public
  sources do not establish that Modus lacks this feature internally.
- Added the public landing route and authenticated `/change-impact` workbench.
- Backend impact analysis is read-only and requires no schema migration.
- Production TypeScript/Vite build passed locally and in Docker.
- Full backend suite: 48 existing tests passed and five new tests passed on
  first run. The sixth test had an incomplete fixture (`relation` was omitted);
  corrected it and reran all six new tests successfully. Total: 54 passing tests
  across the full baseline run and the corrected feature-suite run.
- Browser verified: landing layout, interactive scenario switcher, login return
  to intended route, actual invoice preview, shared ledger with 20 dependent
  assertions and 173 stored current checks, downloaded valid JSON impact report,
  mobile navigation and 390px layout without horizontal overflow.
- Landing scenarios are illustrative. Actual workbench totals come from the DB.
- Local Docker frontend/backend were rebuilt; existing PostgreSQL volume kept.

## September 16, 2026 — Sign-in recovery and plain-language guide

- Reproduced `Could not validate credentials` in the existing browser session.
- Protected API requests now clear a rejected session and send the user to
  login with a readable explanation. Successful sign-in returns to the intended
  page. A late response from an old token cannot clear a newer session.
- Wrong passwords get a clear message; role restrictions do not log users out.
- Report generation now goes through authenticated API requests instead of
  unauthenticated direct links. A visible report-ready link lets users save the
  generated JSON or HTML. Browser verified both report-ready states without a
  credentials error; the in-app browser's saved-file location was not confirmed.
- Added `/guide` with an example, a walkthrough, page descriptions, glossary,
  and clear limits of the sample-data demo. Simplified landing, change preview,
  navigation, login, dashboard, check list, review, risk and report explanations.
- Kept database settings and server keys unchanged. No database reset performed.
- Verification: six frontend authentication/API tests pass; TypeScript/Vite and
  Docker production builds pass. Browser confirmed old-session recovery,
  wrong-password feedback, successful auditor sign-in and return to the change
  preview, the guide, and authenticated preparation of both report formats.

## September 16, 2026 — Dedicated dashboard and persistent navigation

- Replaced the signed-in overview with a dedicated dashboard showing actual
  project totals, open review tasks, progress, recent activity, and quick links.
- All nine signed-in pages and both detail routes now share one workspace
  layout. The landing page remains a separate signed-out experience.
- Added grouped navigation, active states, icons, user information, sign-out,
  persistent desktop collapse, and a mobile drawer with keyboard focus handling.
- Added a searchable Documents library with a document-type filter.
- Sign-in defaults to Dashboard; expired-session return paths are preserved.
- Browser checked every sidebar destination, document search, document and item
  detail pages, collapse persistence after refresh, and successful sign-in.
- At 390px, all nine pages had no page-level horizontal overflow. Verified
  mobile close button, Escape, backdrop dismissal, close-on-navigation, focus
  cycling, and inert background content. No browser console errors observed.
- Corrected recent activity to select the newest events and adjusted the
  mobile backdrop to cover only the exposed area beside the drawer.
- TypeScript/Vite and Docker production builds passed; the six frontend API
  regression tests passed. The rebuilt frontend is running locally.

## September 16, 2026 — GitHub and hosted demo

- Created the public `imranrkhan13/audit-evidence-graph` GitHub repository.
- Published the frontend and FastAPI backend together on Vercel at
  https://audit-evidence-graph.vercel.app and connected main-branch deployments.
- Added the hosted adapter with temporary synthetic SQLite data, stable seeded
  IDs, an initialization lock, and a fresh secret stored in Vercel.
- Hosted screens explain that changes can reset; local PostgreSQL is untouched.
- Ignored private environment files, local databases, build outputs and hosting
  credentials. Source scan found no private environment secret values.
- Validation: 55 backend tests, six frontend tests, TypeScript/Vite build, hosted
  adapter smoke test, and Vercel production build passed. Live browser sign-in
  loaded the expected dashboard totals and document-change tool.

## September 17, 2026 — Real receipt extraction

- Added `/receipts` with photo/PDF upload, explicit processing consent, Interfaze
  structured extraction, original-file preview, field and line-item corrections,
  arithmetic checks, optional expected-total comparison, review state, and JSON
  or CSV exports. Results remain in tab memory and never enter shared demo data.
- Added server-side 3 MB/type/image/PDF validation, a three-page PDF limit,
  authentication, no-store responses, provider timeouts, sanitized errors,
  best-effort per-instance throttling, ZDR and cache-bypass headers.
- Configured the owner-provided key only in Vercel's secret environment storage.
  The owner confirmed free credits only and paid billing disabled. Application
  throttling is not a global spending cap; provider controls remain required.
- Tests: 72 backend and 11 frontend tests passed; TypeScript/Vite build passed.
- A live Interfaze request extracted the correct USD 19.80 total and two line
  items from a clearly labeled, generated synthetic receipt.
- Durable private accounts, cloud receipt storage, and linking real receipts
  into the shared sample audit are intentionally not part of this upload flow.

- Live browser verified the full upload flow, correct extraction of the test
  receipt, edited-total differences, review state and in-tab navigation.
  Export controls use direct download links; in-app saved-file location was
  not confirmed by the browser automation's download event.
