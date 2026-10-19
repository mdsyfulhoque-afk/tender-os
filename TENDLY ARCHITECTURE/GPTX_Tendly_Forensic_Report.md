# GPT-X Forensic Architecture Report — Tendly AI
**Evidence cut-off:** 2026-10-19  
**Basis:** Fourteen user-provided screenshots of public Tendly user-guide pages, plus the user-supplied black-box chat transcripts and search-result screenshots accumulated across earlier probe rounds.

> **Fidelity boundary:** This report reconstructs **observable product functionality** and proposes a **reference implementation**. It is **not** Tendly's original source code, hidden prompt, proprietary schema, confirmed service topology, or production configuration. Every named software module below is hypothetical unless specifically described as a documented product feature.

## Executive findings

1. **The product has multiple visibly distinct functional paths.** The guides describe Chat, Explorer, Categories, Tender Matches, Saved Alerts, Tender Overview, Buyer/Seller Insights, Pipeline, Calendar, Documents, Bid Review, and human expert services. These are documented *user-facing capabilities*, not verified microservices.
2. **Tender Matches has a documented rule-based candidate/score path.** The guide says an open tender is first checked for a CPV-prefix match against company-profile categories, then keyword presence is checked in title, description and CPV category name. A CPV-only match begins at 60/100; keyword matches add points (title weighted most, category name least) up to 100. The guide explicitly says **no language model reads tender documents at this stage**. Up to 500 tenders are written per run. [UG-02]
3. **Chat discovery and structured Explorer search have different apparent matching semantics.** Screenshots show Chat displaying the Lithuanian body-camera notice with primary CPV `35120000` even for CPV `72000000` searches. Tendly describes Chat as using related text/CPV expansion. The Explorer guide documents a typed CPV/category control, but an actual Explorer filtered export has **not** been supplied. [UG-01, UG-10; BB-01, BB-05]
4. **Deadline and notice-stage semantics cannot be inferred from a generic card date.** The DORS+ card displayed 2026-11-23 as a generic closing date; the conversation later identified that as estimated future publication, versus 2026-10-29 for market engagement. The product's ability to *explain* this discrepancy did not cause the card to update. [BB-02 through BB-04]
5. **Explorer's visible `Type` filter is not explicitly a notice-stage filter.** The guide describes values such as e-procurement, traditional, green, and EU-funded. Tendly's conversational claims of strict bidding-stage enforcement are **not verified by this screenshot**. Do not collapse those distinct claims. [UG-10, BB-07]
6. **Bid production and review are real documented feature families, not just tender retrieval.** Tender-scoped document generation, file uploads, company-profile context, tracked Accept/Reject review proposals, a requirements compliance matrix, six-step pipeline, calendar, and human tender experts form a substantial documented execution surface. [UG-05, UG-08, UG-09, UG-12, UG-14]

## Evidence levels and traceability

- `GUIDE`: user-provided screenshot of a named public guide page; documents what Tendly says it supports.
- `UI`: a live-product screenshot supplied by the user; proves only the visible result.
- `SELF-REPORT`: a response produced by Tendly's assistant; useful but may overstate features.
- `CROSS-CHECK`: individual public tender fields discussed in earlier turns; does not verify full architecture.
- `INFERENCE`: our hypothesis or an independent design component.

The attached `evidence_manifest.json` lists filenames, covered topics and SHA-256 fingerprints for **all 14 guide images**.

### Guide-source index

| ID | Guide page | Primary architecture evidence |
|---|---|---|
| UG-01 | Asking the AI assistant | Conversation, tender cards, tool modes, attachments |
| UG-02 | Running AI matching | Rule-based CPV+keyword matching, score baseline, refresh |
| UG-03 | Saved alerts | Alert criteria and email scheduling |
| UG-04 | Researching a buyer | Buyer-spend, competitors, award analytics |
| UG-05 | Deadline calendar | Pipeline calendar and deadline-event labels |
| UG-06 | Browsing by category | CPV industry taxonomy and category tiles |
| UG-07 | Researching a company | Award-based seller analytics and limitations |
| UG-08 | Drafting bid documents | Workspace, linked tender documents, generated files |
| UG-09 | Reviewing your bid | Review cards, compliance matrix, acceptance workflow |
| UG-10 | Searching with Explorer | Structured keyword, CPV, buyer, country, value, deadline filters |
| UG-11 | Understanding your matches | Matching tiers and human triage controls |
| UG-12 | Your pipeline | Six statuses, collaboration, notes and assignments |
| UG-13 | Reading a tender | Tender detail, attached public files, scoped assistant |
| UG-14 | Getting expert help | Human bid preparation and scoped document access |

## Reconstructed functional topology

```text
                     PUBLIC PROCUREMENT NOTICES
                  national sources / EU / NATO / other
                                    |
                [ingestion & normalization: PROPOSED]
            notices | IDs | CPVs | values | stages | dates
                                    |
                 [source-aware records: PROPOSED]
                                    |
              +---------------------+-----------------+
              |                     |                 |
         DISCOVERY              INTELLIGENCE        EXECUTION
              |                     |                 |
  Chat / Explorer / Categories   Tender Overview   Pipeline (6 stages)
  Saved Alerts / Tender Matches  Buyer Insights    Calendar
              |                 Company Insights   Documents/Drafting
     Result cards / filters       Source documents  Review & compliance
     Scores, tiers, decisions    Tender Ask AI      Expert-assisted bids
              |                     |                 |
              +---------------------+-----------------+
                                    |
                       Roles, plans, collaboration,
                          provenance and audit
```

**Important:** The arrows are *logical dependencies inferred for a possible system design*. They do not imply verified direct API calls, database joins, separate runtimes or agent handoffs.

## Documented discovery paths

### Chat assistant [UG-01, UG-13; UI probes]
- The chat receives natural-language tender, buyer and procurement requests and may render matching-tender cards with `Pipeline`, `Overview`, and `Ask AI` actions.
- The guide describes pre-written phase/status phrases such as “Processing request” and “Gathering relevant data”; these are **visible progress labels**, not evidence of named cooperating agents.
- `Ask AI` can pin one tender into the chat context. Product guides describe official-document retrieval when summary fields are insufficient, subject to the source portal providing the file.
- The product text describes file uploads and tools for seller/buyer analysis; exact production file handling is not independently inspected.
- **Observed mismatch:** Chat search for CPV 72000000 included record `9930587` whose only reported official CPV is 35120000. That supports broad results, not an exact filtering guarantee.

### Explorer [UG-10]
- Three primary inputs: **Keywords**, **CPV code/category**, and **Organisation** (buyer). Positive keyword tags are combined; a minus-prefixed term is an exclusion checked against title and description.
- Filter bar: country multiselect; value bands; deadline presets; and a `Type` selector whose guide examples are e-procurement, traditional, green and EU-funded.
- Sorting: newest, deadline soonest/latest, value high/low.
- Result batches are 24 cards, with more loaded on request. A “similar” chip can represent clustered near-identical lots under a framework.
- The guide states only tenders whose submission deadline is in the future are returned; **this is product documentation**, not a tested invariant for every notice type.
- Tendly's assistant *claims* the CPV filter includes descendants and matches both primary and secondary classifications and that CSV/Excel exports follow current filters. **No actual Explorer export or direct screenshot of the executed CPV filter was supplied.**
- The guide's visible `Type` examples do **not** establish a formal-bid/market-engagement filter; verify separately.

### Categories [UG-06]
- The guide describes 46 industries organized into 13 groups, based on CPV codes.
- Category tiles open current tenders with country and time-left controls; card actions are reused.
- Functionally distinct from a typed exact-CPV query, even if underlying records overlap.

### Saved Alerts [UG-03]
- Named alert: comma-separated keywords, CPV codes, selected countries, value range, notification frequency.
- Frequencies in the guide are Real-time, Daily, and Weekly; it describes hourly checks and one notification per tender per alert.
- Alerts are described as **explicit user criteria** rather than company-profile relevance scoring.
- Account required; email notifications and account-scoped history imply persistent alert state, without exposing the actual storage implementation.

### Tender Matches [UG-02, UG-11] — critical mechanism

**Guide-declared candidate selection and score model:**

```text
profile.CPV_categories + profile.keywords + selected_countries
       -> open tender CPV-prefix candidate selection
       -> keyword hits in title / description / category name
       -> score (CPV-only base = 60; max = 100)
       -> tier badge + templated match-reason line
       -> matched list (up to 500 records per run)
```

- Guide: initial score **60** if the tender clears the CPV filter.
- Guide: title keyword hits are weighted more than category-name hits. **Exact weights not published** in supplied screenshots.
- Guide: no language model reads tender documents **at this stage**; do not call this document-RAG scoring.
- Guide: an automatic first run may follow onboarding; manual country selection and credit rules depend on plan; automatic refresh is documented as Tuesday–Saturday.
- Guide: Perfect is 90+, Strong is 75–89. The Possible/Weak threshold is partly hidden under the cookie bar; the 60-point floor makes Weak nearly empty in practice.
- Guide: matches belong to the organization/account, not an individual member; users choose Yes/Maybe/No and can push decisions to Pipeline.

## Intelligence and provenance paths

### Tender Overview [UG-13]
The guide enumerates tender metadata (amount, published and submission dates, country, CPV, NUTS and contracting authority), project timeline, a quality score, evaluation criteria, description with translation, AI-generated requirements summary, attached documents, and personal/team notes. A document request may return original source attachments rather than relying only on stored summaries. **This supports a design need for document-level provenance**, not an inference about vector stores.

### Buyer analytics [UG-04]
Buyer profiles summarize tenders issued, spend/total procurement, average contract value and active notices. The guide also describes monthly patterns, procedure metrics, evaluation/competition summaries, suppliers and spending categories. Completeness varies by country and buyer publications; buyer profiles cannot be presumed exhaustively complete.

### Company/seller insights [UG-07]
Seller profiles summarize public contract wins, award values, average values, sectors, geographic coverage, win history, similar companies and partner/shared-buyer patterns. The guide says:
- Award data contains **winners**, not every participant; a true bid win rate cannot be computed from that data alone.
- Organization spelling variations may result in multiple profiles or duplicated grouping until reconciled.
- A company search returns up to 20 companies; analytics may be cached for up to six hours.
These claims are useful for validation plans but do not expose the award-data backend.

## Execution layer and workflow state

### Pipeline [UG-12]
The six named board columns are **Saved → Qualifying → Drafting → Review → Submitted → Results**. Results supports Won/Lost/Appeal. Cards support reassignment, comments, notes, attachments, filters and team-shared progress. Saving a tender and recording Yes/Maybe/No match decisions can feed this workflow.

### Calendar [UG-05]
Calendar records originate from saved pipeline tenders with relevant dates. Submission and Questions are distinct event types, visually differentiated in the guide. **Important caveat:** the Questions/Q-date is Tendly's *estimate*, explicitly not the buyer's official clarification deadline. This is a separate hazard from the DORS+ future-publication-date mismatch.

### Document workspace and review [UG-08, UG-09]
- Attach an official tender, upload a PDF or office document, optionally use company profile and knowledge-base materials, and request proposal/draft/compliance content.
- Document generation supports editable DOCX, XLSX and CSV; the guide explicitly notes no PDF export in that workspace.
- A user-facing review loop proposes small edits on cards with **Accept**, **Reject**, and **View**; edits are not presumed approved until the user accepts.
- The Compliance Matrix categorizes Eligibility, Technical, Financial, Submission Formalities and Contract Terms, with statuses such as Meet/Gap/To confirm; it is a review aid, not an approval certificate.
- Bid/No-Bid analysis and draft placeholders do not relieve the human signatory of verifying the bid.

### Expert-assisted bid [UG-14]
Human expert service connects a pipeline tender to an expert, with contact details, NDA/service conditions, scoped access to customer materials and review/approval checkpoints. This is not necessarily an autonomous multi-agent software system; it is explicitly a **human service path**.

## Empirical findings from earlier black-box probes

| Finding | Source type | Proper interpretation |
|---|---|---|
| CPV 72000000 Chat search included Lithuanian `9930587` (35120000) | UI + target response | Cross-category Chat retrieval observed; exact internal reason unknown |
| Tendly said body-camera notice had no secondary IT CPVs | SELF-REPORT; individual notice cross-check discussed | Supports negative control for strict Explorer CPV test |
| DORS+ Chat card labeled Nov 23 as closing, AI later identified future publication | UI + SELF-REPORT | Deadline field semantics inconsistent in sampled Chat result |
| DORS+ UK2 planning notice appeared in Chat's strict live-bidding query | UI + SELF-REPORT | Formal-bid restriction not enforced on sampled Chat results |
| Chat correction did not rewrite tender card | SELF-REPORT + retained card | No demonstrated persistent correction |
| Explorer exact CPV and bid-stage behavior | SELF-REPORT + guide-description | Not independently tested in Explorer; do not mark verified |
| Unexpected discussion of excluding keyword `use` | UI | Potential parsing anomaly, insufficient to prove a tokenization mechanism |

## Proposed, independent deployable reference architecture

**This is an engineering proposal, never a claim about Tendly's proprietary implementation.**

**Ingestion and canonical records**
- Store original source payloads immutably with portal URL, publication time and snapshot metadata.
- Parse tender identity, buyer identity, CPV list (primary/secondary), procedure stage, amounts and all date-event labels.
- Preserve both original native-currency/amount/VAT basis and derived conversions with rate source/timestamp.
- Use typed events: `submission_deadline`, `market_engagement_due`, `clarification_due`, `estimated_publication`, `award_date`.
- Preserve official notice ID and OCID independently from platform-specific record IDs; link notice versions to procurement lifecycle.

**Search**
- Explorer must implement selected semantics deterministically: `cpv_exact`, `cpv_descendants`, `include_secondary`, country, value, buyer, deadline event type and procurement stage. The UI must not claim an exclusion that result cards contradict.
- Chat can broaden with *separately labeled* related results. Do not represent 35120000 as an exact IT-services CPV match.
- Sort and pagination must explicitly state the ordering rule; change of sort may change the card sequence.
- Keep candidate scores and match justifications auditable. Do not claim the documented 60-point Tendly weights are its source formula; only what is visible.

**AI/document analysis**
- Retrieval should favor official notice PDFs, attachments or OCDS records where lawful and available, and cite them.
- Distinguish source extraction, AI-generated synthesis, user-uploaded documents, and generated text.
- Require explicit acceptance of all document edits, and preserve prior versions.
- Reserve a human approval step for regulatory claims, eligibility and final submission.

**Execution**
- Use an organization-scoped pipeline state machine, annotated deadline-event calendar, repeatable alert matcher and deduplicated notification log.
- Expert service should be governed by explicit permissions and revocation.
- Analytics should aggregate public award records and report missingness; do not infer bid win rates without denominator data.

**Illustrative core entities**: `source_portal`, `notice`, `notice_version`, `procurement`, `notice_cpv`, `deadline_event`, `tender_document`, `organization`, `award`, `company_profile`, `match_run`, `match_score`, `saved_alert`, `pipeline_item`, `calendar_item`, `generated_document`, `revision_suggestion`, `expert_assignment`, `audit_event`.

## Reproducible validation plan

The included YAML provides 13 acceptance tests. The highest-priority are:

1. **CPV negative control:** In Explorer search Lithuania + 72000000 (including descendants); tender `9930587`, officially classified as 35120000, must not qualify unless an additional official IT CPV exists.
2. **Stage negative control:** UK strict formal-bid Explorer search must exclude DORS+ `T-2052111748` if its stage is still UK2 preliminary market engagement.
3. **Date semantic control:** DORS+ 2026-10-29 engagement due date and 2026-11-23 estimated future publication must be presented as **different event types**, never mapped to one generic final-bid deadline.
4. **Matching repeatability:** Same CPV/keyword profile and same notice snapshot should yield consistent relevance scores and tiers.
5. **Export fidelity:** Obtain actual Explorer CSV/XLSX, compare exact columns with original notice fields, and test filter/result-set alignment. **Column names remain unknown.**
6. **Document review integrity:** Verify only user-accepted edits persist to the generated document, and source quotations/citations survive revision.

## GPT-X analyzer integration (separate from Tendly architecture)

The user-provided GPT-X deployment bundle contains `IntegratedAgentSchema.yaml`, declaring `CitationValidatorAgent`, `SectionGeneratorAgent` and `ExportAgent`. This is **your GPT-X tool configuration**, not Tendly's code.

A proposed GPT-X forensic sidecar can implement these analytical roles:
- `ProbePlanner`: select one changed input for each A/B test.
- `EvidenceLedger`: attach screenshots/notices and their field-level provenance.
- `HypothesisTracker`: keep observed, reported, inferred and falsified assertions separate.
- `DifferentialComparator`: compare Chat/Explorer matches, deadlines, IDs, stages and CPVs.
- `SchemaSynthesizer`: produce the YAML functional specification.
- `ReportExporter`: package findings and test cases.

Do not transplant the original GPT-X `CitationValidatorAgent`'s CrossRef/PubMed fallbacks directly to procurement; those are publication/biomedical sources. A procurement-specific fallback chain should be separately designed around official notice portals, authoritative mirrors, and OCDS record links.

## Unresolved facts — not to be claimed as recovered
- Tendly source code, actual hidden prompts, tool invocation schema, proprietary database ERD
- Runtime model provider or deployment, embedding model, ranking formula or exact search-index technology
- Whether physical Chat and Explorer services share one index or multiple query services
- Whether a formal notice-stage filter exists in Explorer beyond the guide's documented `Type` field
- Exact exported CSV/XLSX headers, primary/secondary CPV representation and deadline-event columns
- Whether all 28 advertised markets have equivalent data completeness and normalized publication semantics

## Artifact contents

- `GPTX_Tendly_Functional_Architecture.yaml`: structured, valid YAML model (documented features, observations, hypotheses, proposed reference layers, 13 test cases).
- `GPTX_Tendly_Forensic_Report.md`: this evidence report.
- `evidence_manifest.json`: file-by-file screenshot provenance and SHA-256 fingerprints.
- `Original_GPTX_IntegratedAgentSchema.yaml`: extracted **unchanged** from the user's own GPT-X deployment bundle (not sourced from Tendly).
- `guide_screenshots/`: 14 original user-provided guide images.

**Bottom line:** We now have enough public, supplied evidence to specify and build a *separately implemented product* with similar user-facing workflows. We do **not** have evidence to reproduce Tendly's hidden code verbatim or assert its private system architecture.
