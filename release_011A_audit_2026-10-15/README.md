# Proposal Guard Release 011A Preservation and Integration Audit

Audit date: 15 October 2026, Asia/Dhaka client date.

Release 011A inspection and evidence collection are complete. Preserve Proposal Guard as the application and extend its existing Python, Streamlit and SQLAlchemy architecture. Release 011 is a compatible partial repair candidate, but its patches are not integrated into the current application. The broader safety contract still has reproducible failures in both copies. Proceed to a controlled Release 012 repair before treating an eligibility recommendation or readiness label as approved bidding clearance.

The authorized scope for this delivery is the pasted Release 011A blueprint. The attached Markdown and DOCX were read as design references. Their historical statements, approval labels, external website checks and earlier test reports were not treated as current execution evidence. Releases 012 through 017 remain proposed development work.

## Evidence and preservation

| Evidence | Verified result |
| --- | --- |
| Current application | `../tenderproof_os` |
| Source ZIP | `../ProposalGuard_Source_Audit.zip`; 74 files; SHA-256 `8a3f4b2a5c8aa8e86bd47c47906dba4c3621cbb508383290132f41a9eba6ca55` |
| ZIP versus current application | All 74 archived files match the corresponding current files byte-for-byte |
| Operational project inventory | 340 files, including source, seed/reference assets and persistent storage |
| Application Python modules | 57, including tests |
| Existing UI | 16 Streamlit pages retained |
| Database | 17 tables; SQLite integrity check `ok`; one case; 52 requirements; 52 compliance rows; five sources |
| Data relationships sampled structurally | No orphan case links or compliance-to-requirement mismatches; no missing registered source/output files |
| Backup | All snapshot members read back and hashed; restored SQLite integrity and all 17 table row counts match |
| Preservation check | See `preservation_check.json` for the final comparison of all inventoried operational files and the source ZIP |

The inventory excludes `.venv`, `.git`, `__pycache__`, `.pytest_cache` and temporary image-rendering files under `tmp`. These exclusions are explicit in the backup manifest. Installed dependency versions are captured separately. This is a verified source-and-data recovery snapshot; it does not claim to preserve Windows, OneDrive metadata or the virtual environment itself.

No application source, schema, saved records or existing output files were changed by the audit. All executed application code ran from copies under `isolated/`. The live database was inspected through SQLite `mode=ro` with `query_only=ON`. Test-created documents, demo cases and databases are confined to audit copies and temporary test directories.

## Test results

| Check | Current application | Temporary Release 011 candidate |
| --- | --- | --- |
| Existing regression suite | 27 passed | 34 passed, including seven added Release 011 checks |
| Additional proposed safety contract | 2 passed, 22 failed | 8 passed, 16 failed |
| Streamlit page smoke test | 16 of 16 rendered without exceptions | 16 of 16 rendered without exceptions |
| Public function signatures in the three changed services | Compatible with candidate | Unchanged public signatures |
| Database/model changes in candidate | None | None |

The additional 24 probes use synthetic data and call the actual service functions. Failures are recorded as failures, not hidden with expected-failure markers. They exercise the requested future acceptance contract; some identify missing capabilities beyond the original MVP. They are not 22 or 16 independent defect counts, and the two passing controls do not establish procurement accuracy.

The UI checks use Streamlit AppTest with a synthetic demo case. They demonstrate page execution and import compatibility, not complete interactive acceptance of every edit, upload, download, Windows launcher, OCR output or live e-GP workflow. No production portal, external AI API or customer-benefit benchmark was exercised.

Detailed commands, JUnit results and captured outputs are in `test_results/`. `SAFETY_TEST_MATRIX.csv` compares each acceptance probe across both versions.

## Findings

### F01 High priority Positive recommendations ignore mandatory eligibility

`tenderproof/services/bid_score_service.py:54` derives missing inputs only from scorecard values; line 55 chooses the recommendation from the aggregate percentage. A synthetic case with all ten categories scored 5 receives `Pursue` even when a mandatory requirement is Gap, Pending Input, Partially Met or Not Applicable without a reviewed exclusion. Requirement review state does not govern that decision.

Release 011 blocks these four cases and unreviewed requirements while retaining opportunity-score calculations. Integrate this behavior as a first repair, then use one shared final-decision policy. Preserve the distinction between a confirmed failure and missing evidence: the candidate treats every `Gap` as rejection, although the current model also uses Gap for evidence that has not been supplied. No numeric turnover, period, unit or company qualification comparison exists yet.

Evidence: `test_mandatory_unresolved_blocks_positive_recommendation[...]`, current versus candidate results in `SAFETY_TEST_MATRIX.csv`.

### F02 High priority Source and evidence changes can reuse stale readiness

Current `source_service.py:14` registers new sources without invalidation. Release 011 adds immediate source invalidation, but re-running verification can immediately clear the amended case using only old requirements. Neither version establishes that all relevant clauses from the new source version have been extracted, reviewed and evaluated.

Requirement updates in `extraction_service.py:68` and compliance updates in `compliance_service.py:45` leave readiness unchanged in both versions. A later report can still contain `Readiness label: CLIENT_READY` after mandatory evidence has been removed. Source hashing, content versions, dependency snapshots and an approval invalidation model are absent.

Evidence: source invalidation improves in candidate; amendment re-clearance, requirement/evidence invalidation and stale-report probes fail in both. Any integration must invalidate dependent recommendations, verification, approvals and output eligibility, while retaining historical records.

### F03 High priority Any nonempty evidence string can support a ready label

`verification_service.py:61` enforces only the empty-string/status consistency rule. A mandatory row marked Met with `Pending Input`, an explicitly expired license, or a license attributed to another legal entity can produce `CLIENT_READY` in the controlled probes. Release 011 checks Met plus nonempty text, so it also fails these cases.

This demonstrates a missing structured evidence-validation capability. A phrase parser alone is not an adequate repair: store evidence identity, source, legal entity, validity interval, relevant period, review result and reviewer, then evaluate the applicable typed rule against those records. Human review must remain explicit where the evidence cannot be validated deterministically.

### F04 High priority Incomplete extraction and pending e-GP work do not block readiness

`verification_service.py:45` accepts any truthy extraction status, including `failed`, `empty` and `partial`. The existing e-GP checklist is not consulted by the verification engine. Both copies can produce `CLIENT_READY` with these source statuses or with all applicable e-GP checklist items pending in the synthetic case.

Separately, `source_service.py` chooses the PDF text layer by aggregate character count and caps OCR at 200 pages. It does not persist page-by-page processing completeness or confidence. Its OCR unit test mocks recognized text and demonstrates page iteration, not Bangla recognition quality. Processing coverage, reviewed scope and extraction failures must be explicit prerequisites for release.

### F05 High priority Human approval and protected release transitions are absent

There is no user, reviewer approval, assessment version or approval snapshot table. `case_service.py:70` permits generic updates to `readiness_label`; case creation also accepts a supplied ready label. Both copies accept direct assignment of `EXPORT_READY` in the service probe despite unresolved mandatory requirements. `report_service.py:29` and `export_service.py:56` generate artifacts without an authoritative approval/freshness gate.

The app currently stores a recommendation and readiness label, not an auditable approved-BID decision. Do not equate a `Pursue` score recommendation with human authorization. Add a local, attributable review and approval event tied to the exact evidence snapshot; this does not require converting the product into a public multi-tenant SaaS.

### F06 Medium priority Warnings and failed verification appear completed

`verification_service.py:141` and line 143 return ready labels based on existing outputs before the warning branch at line 145. A case with a verification warning can therefore be marked `CLIENT_READY`. `workflow_service.py:31` considers verification complete when any result rows exist, including a failed run. Both behaviors fail the synthetic probes in both versions.

Apply blocker and warning precedence before artifact-based promotion, and make workflow completion depend on the latest current successful run and approval.

### F07 Medium priority Exported spreadsheet text can become a formula

`export_service.py:68` writes untrusted string values through pandas/openpyxl without enforcing literal text. A harmless test value `=1+1` in the client name is stored as an Excel formula cell in both versions. Export inputs can include client and source material; normalize such values as text and verify the actual stored cell type. Retain all 16 existing workbook sheets.

### F08 Medium priority Audit history and operational safeguards need extension

`verification_service.py:26` deletes prior rule rows on each run; Release 011 invalidation also deletes them. Existing audit messages do not preserve the underlying full evidence or approval snapshot. `ui/tor_extraction.py:58` sends edited text to both the atomic and original requirement text fields. The original uploaded document is retained, but the normalized row does not maintain an immutable source quotation.

The current database has zero declared foreign keys and `user_version=0`. `db.py` performs two inline additive column checks without a versioned migration journal. No current orphan links were found; that clean state does not enforce future consistency. Duplicate logical questions and risks are prevented by existing service logic and passing idempotency tests, but most logical uniqueness rules are not database-enforced.

The Git repository is on `master` with no commits and the application is untracked. A Git reset cannot currently provide an application rollback. Preserve the recovery snapshot, establish a reviewed baseline later, and use additive versioned migrations with restore tests.

### F09 Medium priority Tests and installation are not reproducibly isolated

The existing pytest fixture isolates its SQLite file but report and source services use project-level storage constants. Running the ordinary launcher test command can therefore create test documents in operational storage. This audit avoids that behavior by testing copies. Extend the fixture/configuration to isolate every output path.

Dependencies are specified using open-ended minimum versions. `deploy&run.bat:44` and line 50 upgrade/install on every run. The tested environment is Python 3.14.5 on Windows, Streamlit 1.58.0, SQLAlchemy 2.0.50 and pandas 3.0.3. `pip check` reports no broken requirements. Python 3.11 compatibility, package vulnerabilities and installation on a clean machine were not verified.

RapidOCR 3.10.0 with ONNX Runtime 1.31.0 is installed. The app uses its default OCR configuration rather than a pinned application model/language policy. The default model list inspected earlier does not list Bangla. Human-checked Bangla and mixed-layout fixtures are required before using OCR as qualification evidence. No external AI provider integration exists in the app.

## Release 011 integration disposition

Only these existing application files differ substantively from the candidate:

| File | Candidate change | Disposition |
| --- | --- | --- |
| `tenderproof/services/bid_score_service.py` | Mandatory requirement/review guard around final recommendation | Integrate with explicit FAIL versus UNKNOWN semantics |
| `tenderproof/services/verification_service.py` | Adds `ELIG-001` mandatory evidence/review blocker | Integrate, then extend evidence/freshness/approval policy and preserve prior runs |
| `tenderproof/services/source_service.py` | Invalidates readiness and output labels after new sources | Integrate the invalidation behavior while replacing history deletion with versioned supersession |

The candidate adds `tests/test_release_011.py` with seven checks and contains a patching helper and saved test log. Existing models and public function argument signatures are unchanged. All original tests remain present; candidate regression results reproduce the reported 34 passes.

The candidate omits the live project's launcher files, `.streamlit` configuration and `.gitignore`. Replace neither the whole project nor its storage with that temporary tree. Use the reviewed three-file diff and tests as input to Release 012. `release011_changes.patch`, `release011_diff.csv` and `api_compatibility.json` provide the concrete comparison. No candidate patch was applied during this audit.

## Existing functionality and architecture

`app.py` is the Streamlit entry point; `run_app.py` and the two Windows launchers initialize and launch it. Navigation dispatches each page with a SQLAlchemy session; `get_session` commits on success, rolls back on exception and closes the session. There are no application REST API routes or service authentication boundaries.

The established service workflow is case creation, source registration, rule-based normalization, compliance/gap mapping, CV evidence, opportunity scoring, risk/methodology planning, report/workbook generation, IP capture and verification. The workflow optimizer and Bangladesh e-GP checklist extend this path. The architecture and function/import index are in `architecture.json`; the complete file dispositions are in `IMPLEMENTATION_MANIFEST.csv`.

Preserve these 16 pages: Home / Command Center; Workflow Optimizer; Bangladesh e-GP Readiness; Create or Open Case; Upload / Register Inputs; ToR Extraction; Compliance Matrix; CV Matcher; Bid/No-Bid Scorecard; Risk Register and Gaps; Proposal Skeleton and Methodology; Diagnostic Report Generator; Excel Export; IP Capture; Verification / Audit Log; Settings.

Reports retain 14 diagnostic sections plus the e-GP readiness section, generated timestamps and review footer. The workbook currently has 16 sheets, including e-GP Readiness; README's 15-sheet statement is stale. The export page creates workbook files but lacks the in-app download control already present on the report page.

The 17 database tables are cases, sources, normalized_requirements, compliance_ledger, cv_matches, bid_scorecard, bid_recommendations, risk_register, gap_items, clarification_questions, proposal_skeleton, methodology_outline, audit_events, verification_results, ip_capture, output_packages and egp_checklist_items. Column definitions, indexes, row counts and relationship checks are in `database_schema.json`.

## Tender-to-Fit scope assessment

| Functional area | Current evidence | Required extension |
| --- | --- | --- |
| Official tender intake | Generic case metadata and PDF/DOCX/TXT/manual source intake | Tender ID, reference, procuring entity, method, official provenance and versions |
| Company qualification vault | Case organization text and CV rows | Reusable legal-entity, financial, experience, personnel/equipment and certificate evidence |
| Clause analyzer | Rule-based sentence normalization, keys, synthetic auto section references and review flag | Real page/clause provenance, typed values/units/periods, source coverage and human confirmation |
| Eligibility engine | Opportunity percentage; limited presence/status checks | Typed deterministic qualification, evidence validity and explicit PASS/FAIL/UNKNOWN |
| Company-specific tender matching | Not implemented | Ranking subordinate to eligibility and capacity |
| Bid readiness workspace | Generic workflow steps, gaps, risks and 19 e-GP checks | Linked company/tender tasks, forms, owners and deadlines |
| Reports and exports | Markdown, DOCX and XLSX available | Current approved evidence snapshots and e-GP assessment outputs |
| Amendment monitoring | No source versions or automated watcher | Manual amendment invalidation first; authorized source monitoring in Release 017 |

No OpenAI API, live e-GP discovery or authenticated portal integration was introduced. Website availability, supported APIs, source permissions and current legal applicability require separate verification when that release is undertaken. The historical reference documents' legal and website claims were not independently re-certified by this source audit.

## Next controlled development work

Release 012 should integrate the three compatible candidate changes with the missing central eligibility, freshness and local approval gate, protect direct readiness mutations, retain verification history, isolate tests and fix literal spreadsheet export. Keep existing artifacts usable as clearly labeled drafts.

Release 013 adds manual official tender intake and company qualification profiles linked to existing cases/sources. Release 014 adds typed requirement/evidence validation. Release 015 adds ranking, tasks and the complete manual Tender-to-Fit pilot. Release 016 extends approved reports and optional AI extraction after a human-reviewed benchmark. Release 017 adds authorized discovery and amendment monitoring after source access and reliability are verified.

Use `IMPLEMENTATION_MANIFEST.csv` for KEEP / REPAIR / EXTEND / ADD decisions, dependencies, risks and acceptance checks for every inventoried file and each proposed new file. `BACKUP_AND_MIGRATION_PLAN.md` defines the preservation and rollback procedure. No later release is represented as implemented or approved.

## Delivery gate

Current phase: Release 011A preservation and integration audit complete. Source integrity, backup recovery and existing regression compatibility pass. The proposed decision-safety contract fails on both application versions. Production and approved-client-decision readiness are blocked by the findings above; a numerical readiness percentage is not measured. No customer willingness-to-pay or time-saving claim was tested.

Next engineering step: implement Release 012 from the reviewed manifest in an isolated development branch/copy, then require the existing regressions, expanded safety contract, real-database migration/restore checks and full manual-workflow acceptance to pass before release.
