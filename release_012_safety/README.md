# Proposal Guard Release 012 Safety Integration Review

Release 012 engineering and fresh automated verification are complete in this isolated working copy. The candidate passes all 24 original safety checks and the full 84-test suite. All 16 pages pass both live-browser navigation checks and Streamlit AppTest smoke checks. The original application, its 340 inventoried files, and its source ZIP remain unchanged. Merge authorization is pending the user's review.

## Review artifacts

| Artifact | Purpose |
| --- | --- |
| `tenderproof_os/` | Working Release 012 application, restored from the verified original baseline and incrementally repaired |
| `CHANGE_MANIFEST.csv` | All 31 changed or added application files, rationale, before/after hashes, verification and rollback references |
| `release_012_review.patch` | Full review diff, including added files |
| `release_012_changed_files.zip` | The 31 code/document/test files only; no operational database or client storage |
| `evidence/verification_summary.json` | Fresh automated gate summary and individual test outcomes |
| `evidence/verification_audit.xml` and `.log` | Full 84-test verification run, zero failures/errors/skips |
| `evidence/independent_safety.xml` and `.log` | Separate fresh process running the original external 24-check audit file, all passed |
| `evidence/unchanged_safety_tests.json` | Byte-for-byte confirmation that the 24 safety checks and seven Release 011 tests were not weakened |
| `evidence/page_smoke.json` | 16-page AppTest results |
| `evidence/browser_verification.json` | Recorded live-browser observations for all 16 pages after worker restart |
| `evidence/recovery_check.json` | Migration, repeat initialization, backup restoration and original-value preservation results |
| `evidence/preservation_check.json` | Hash comparison proving the original project and source ZIP are unchanged |
| `tenderproof_os/RELEASE_012.md` | Operator workflow, scope, migration and preview runbook |

The separate safety process is an independent execution of the unchanged test file, not a claim that a second human auditor has approved the release. Earlier engineering logs, including an intermediate UI interaction failure and its fix, remain under `evidence/`.

## Acceptance ledger

| Gate | Result | Evidence |
| --- | --- | --- |
| G01 All 24 additional checks pass | PASS, 24/24; no skipped or expected-failure cases | `independent_safety.xml`, unchanged file hashes |
| G02 Existing and new regressions pass | PASS, 84/84, including the original 27 and seven Release 011 checks | `verification_audit.xml` |
| G03 Mandatory failure never supplies positive clearance | PASS; mandatory uncertainty/failure takes precedence and final release uses verified policy | Original safety matrix and positive/negative workflow tests |
| G04 Missing, invalid, expired or wrong-entity evidence blocks clearance | PASS; explicit evidence review records, legal entity, validity, file integrity and source review required | Workflow mutation and natural-expiry tests |
| G05 Relevant amendments invalidate dependent approval | PASS; conservative invalidation on new source versions plus source/requirement/evidence fingerprints | Source-change and amendment regression tests |
| G06 Unapproved or stale output cannot appear client-ready | PASS; shared release policy, versioned artifacts, metadata and content hashes, protected preview/download | Original safety checks and altered-report UI test |
| G07 Existing pages and workflows preserved | PASS for tested scope; 16/16 browser and AppTest renders; approved report/workbook and UI confirmation workflows pass | Browser/page evidence and workflow tests |
| G08 Existing data integrity and rollback verified | PASS; all old fields/values preserved in 17 tables; 21 tables after migration; restore matches old schema/data; injected DDL failure rolls back | Recovery evidence and migration tests |
| Merge and operational release | PENDING USER AUTHORIZATION | No operational merge, database migration or replacement performed |

## Implemented repairs

The existing score calculations and recommendation thresholds remain available. The recommendation service now applies the reviewed mandatory-condition guard before producing a provisional opportunity recommendation. A score alone never supplies release clearance. Confirmed failed evidence produces a failure; missing, partial, unreviewed or unjustified excluded requirements remain unresolved.

A shared decision policy checks active source versions, extraction completeness, source and evidence hashes, legal entity, validity, requirement review, applicable checklist state, current verification and explicit approval. The engine exposes PASS, FAIL and UNKNOWN separately from commercial attractiveness. Validity uses Asia/Dhaka calendar dates. It does not claim to implement the later typed financial/company qualification engine.

Sources retain hashes, versions and supersession links. Manual text retains its exact original bytes alongside normalized extraction. Empty, undecodable, unreadable or partially processed inputs are explicit failures or pending work. New sources and changes to requirements, compliance, evidence, case details, scoring or checklist state invalidate previous clearance. Physical file removal/change and natural evidence expiry also prevent release when evaluated.

Verification stores complete serialized assessment inputs and historical rule results. Named evidence reviews include provenance, legal entity, validity, rationale and reviewer. File-path evidence is archived while the original path remains monitored. A human approval references the exact successful verification run and fingerprint; revocation and later changes cannot reuse it for new current outputs.

Markdown, DOCX and XLSX outputs receive unique filenames and retain historical versions. Reports show draft/blocked/approved state, every requirement's references, evidence reviews and approval provenance. Workbooks retain all 16 sheets, label provisional scores separately, and encode untrusted formula-shaped strings as literal text. Altered or stale approved documents cannot be previewed or downloaded as current approved artifacts.

The existing Verification / Audit Log page now provides source review, evidence review, human confirmation, approval/revocation and history tabs. The navigation still contains the original 16 pages. Readiness labels and counts are evaluated against current policy rather than trusting cached database labels.

## Data preservation and recovery

The candidate was created from the audited snapshot in `../release_011A_audit_2026-10-15/backup/project_snapshot.zip`. All 340 inventoried original application/data files and the original source ZIP retain their hashes. The original operational database was not initialized or migrated.

Migration `012_safety_1` preserves the original fields and rows, adds review/provenance fields, and adds four tables: evidence_reviews, verification_runs, decision_approvals and schema_migrations. Nonempty databases receive a consistent pre-migration backup. Explicit SQLite transactions cover table creation, additive columns and the journal entry.

The recovery rehearsal migrated a restored copy of the actual preserved database. Every original column/value fingerprint in all 17 old tables matched after migration. SQLite integrity and foreign-key checks passed. A second initialization left the migrated database bytes identical. Restoring the automatic backup reproduced the original 17-table schema and row-value fingerprints. An injected mid-migration failure also left the old schema and data intact.

Recovery paths and checks are recorded in `evidence/recovery_check.json`. Existing absolute source/output paths were preserved. The runnable preview uses a separate synthetic database so that reviewing this candidate does not alter client records or depend on relocating those paths.

## Run the isolated preview

The preview is running at `http://localhost:8512` on this workstation. Its database is under `preview/storage/`, separate from both the original app and the copied legacy database.

Double-click `preview_release_012.bat` to start the review preview when it is stopped. It uses the existing verified Python environment. The launcher prints the actual URL if the preferred port is occupied. Avoid starting repeated copies while the current preview is already running.

For a fresh verification run from this directory:

```powershell
& '..\tenderproof_os\.venv\Scripts\python.exe' -X utf8 -B '.\verification_audit.py'
```

This command tests the candidate in isolated runtime directories, reruns the unchanged external safety contract, rehearses migration/restore and rebuilds the review manifest/package. Browser navigation observations are a separate recorded verification step.

## Limits and approval recommendation

Engineering gates pass for the verified local scope. Recommend human review of the change manifest, diff, evidence and rollback procedure as the next merge checkpoint. No merge into the original application is authorized or performed by this package.

Reviewer names are attributable operator entries on the trusted local workstation, not a new authenticated multi-user identity system. There is no public service, e-GP portal automation, external AI integration, tender-specific financial calculation engine, Bangla OCR accuracy certification or customer-benefit benchmark in this release. Professional review must still establish whether the actual supporting document proves the tender clause.

The existing Windows launchers are retained; this review did not install dependencies on a clean Windows/Python environment or independently certify every optional OCR backend. Browser screenshots were captured and visually inspected in tool output, but an optional screenshot-file export was blocked by the browser's HTTP(S)-only URL policy; no saved screenshot file is claimed.

Approval recommendation: accept Release 012 for the human merge review, retain the preserved original and tested recovery point, and keep e-GP feature expansion gated until the user authorizes the reviewed integration.
