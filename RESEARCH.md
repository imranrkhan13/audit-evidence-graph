# Modus research → Evidence Change Impact

Research date: September 15, 2026. Scope: official website, company insights index, publicly accessible LinkedIn company/founder posts, X-indexed material, investor writing, launch coverage, and YC company listings. This is a targeted public-source investigation, not access to the company's internal roadmap.

## Finding

**Build a read-only evidence change-impact workbench.** Given a source document, trace dependent assertions, current checks, prior approvals, and earlier source versions. Let a reviewer preview an invoice amount against its ledger entry before deciding what to reassess.

This is a plausible extension of Modus's stated priorities, **not a verified unimplemented request from Modus**. No reviewed public source establishes whether they have this capability internally. Confirm that with the product team before pitching it as a gap.

## Evidence and source coverage

| Source | Observation | Product implication |
| --- | --- | --- |
| [Modus homepage](https://modusalliance.com/) | The company advertises Andi, automated fieldwork, PBC tracking, intelligent scheduling and faster audits with fewer questions. | Do not pitch basic request tracking or fieldwork automation as new. Extend the existing workflow to later evidence changes. |
| [Modus advantages](https://modusalliance.com/advantages/) | Speed and quality are central positioning. | A narrower, explainable review scope fits both goals. |
| [Modus company page](https://modusalliance.com/company/) | The mission combines an AI transition for accounting firms with less painful accounting services. | Focus on a practical reviewer workflow rather than a generic chatbot. |
| [Company LinkedIn](https://www.linkedin.com/company/modus-audit-inc/) | Public reposts include the CTO's Excel assistant demonstration and emphasis on clearer documentation and higher-judgment work. | Preserve source context, evidence links, and human conclusions. The Excel assistant is already demonstrated. |
| [Lightspeed investment thesis, April 7, 2026](https://lsvp.com/stories/building-the-worlds-first-ai-native-audit-technology-our-investment-in-modus/) | Investor describes manual evidence gathering, extensive back-and-forth, close auditor collaboration, and seven deployed workflows. | A workflow that explains the scope of re-review is a reasonable adjacent hypothesis. |
| [Modus insights index](https://modusalliance.com/insights/) | Lists pieces about AI accounting agents, data governance, and audit preparation. | Relevant context; full article bodies could not be retrieved, so no article-specific claims are inferred. |
| [Techmeme launch archive](https://www.techmeme.com/260408/p1) | Indexes X launch posts by the founders, Lightspeed and Garry Tan. | Supports company identity and launch context, not an unimplemented feature claim. |
| [Indexed CTO X profile](https://ww.twstalker.com/PranavAPillai) | Mirror surfaced posts about auditor shadowing and feedback loops. | Secondary discovery only; not used to establish feature availability. Direct X search was limited. |
| [YC Modus listing](https://www.ycombinator.com/companies/modus) | Founders and product describe a different headcount-management business. | Excluded as evidence about Modus Alliance. A founder's YC ties do not establish a YC batch for this company. |

## Existing project vs. addition

The repository already implements evidence links, deterministic reconciliation, document amendments, selective reruns, review decisions, risk scoring, and evidence search. Those are not new work from this iteration.

The new feature adds:

- Authenticated current-document discovery within a selected engagement (UI uses the first demo engagement).
- Dependency analysis over both primary source references and supporting evidence links.
- Backward traversal of real document-version pointers, with engagement boundaries.
- Counts of linked/unrelated assertions, current rule results, and prior approval records.
- An explicit warning when an evidence link still targets an earlier source version.
- Read-only proposed invoice total comparison against a single USD ledger row. Ambiguous ledger matches produce no numeric comparison.
- Deep links to assertions and original documents, plus a downloadable JSON impact preview.
- Public responsive landing page, styled after the reference's charcoal, blue, serif headline and sans-serif body typography. Georgia substitutes for its proprietary ABC Gramercy font.

## Boundaries

The preview does not rerun checks, invalidate sign-offs, assign work, mutate the evidence graph, or establish audit sufficiency. Approvals are counted as historical approval records, not distinct reviewer conclusions. Graph scope is limited to recorded evidence dependencies; it is not an accounting ontology. Invoice amount comparison is not a complete audit procedure. The existing amendment endpoint has fixture-specific assumptions and is unchanged by this addition.

The public scenario switcher uses clearly labeled fixed illustrative data. The authenticated workbench derives its results from the actual seeded backend. All content is an independent portfolio prototype; no official Modus integration or affiliation is claimed.
