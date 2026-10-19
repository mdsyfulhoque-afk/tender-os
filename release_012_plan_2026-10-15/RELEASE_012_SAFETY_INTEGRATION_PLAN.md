# Proposal Guard: Release 012 Controlled Safety Integration

**MOCK / DRAFT — requires human approval before implementation**

Review date: 15 October 2026, Asia/Dhaka client date. Plan status: `pending_approval`.
Implementation authorization: `pending_approval`. Merge authorization: `pending_approval`.
Task board: **LOCKED**. No application code, data, schema, dependencies, or running server was changed for this planning review.

## 1. Intake and boundaries

**Objective:** repair decision safety in the existing local Python/Streamlit/SQLite application without replacing Proposal Guard or losing its saved work. Commercial operation remains a cash-first internal diagnostic service, not public SaaS.

**Problem:** the operational application passes its historical regression suite but can confuse attractive opportunity scores and existing artifacts with current, evidenced, human-approved clearance. Release 011 is a partial repair, not a release-ready replacement.

**Preserve:** all 340 inventoried files and their recovery copies; existing case IDs, records, uploads, extracted text, reference/seed assets, prompts, templates, reports and exports; all 16 navigation pages; existing service entry points, report sections and workbook sheets; both Windows launchers.

**In scope:** mandatory eligibility guards, structured evidence review, source versions and completeness, assessment freshness, explicit local approval, safe workflow completion, draft/blocked/approved output distinctions, literal spreadsheet text, additive migration and tested recovery.

**Out of scope:** company qualification vault, full numeric financial/experience qualification engine, new tender discovery/ranking, portal scraping or submission, amendment watchers, external AI/SLM APIs, model training, Bangla OCR certification, billing, complex authentication, multi-tenancy and unrelated products. Existing e-GP functionality stays available; expansion waits for safety gates and a separate scope approval.

**Assumptions requiring confirmation at approval:** trusted local operator; named local approval is acceptable without multi-user authentication; Asia/Dhaka calendar dates govern evidence expiry unless the tender specifies otherwise; an unreviewed new source is potentially relevant until explicitly reviewed. No claim is made here about current procurement law or portal access rights.

## 2. Reviewed locations and evidence classification

Workspace: `C:\Users\IP3 Consulting Ltd\OneDrive\Documents\Proposal Guard`.
All relative paths below resolve from this workspace unless marked application-relative.

| Classification | Location / conclusion |
| --- | --- |
| OBSERVED | Operational application is `tenderproof_os/`; actual stack is Python, Streamlit, SQLAlchemy and SQLite, not AgentForge's TypeScript architecture. |
| OBSERVED | Reviewed current scoring, verification, workflow, source, case, extraction, report/export, database/config/launcher paths and UI call sites; inspected the 24-probe test source and Release 011 patch/signature comparison. |
| OBSERVED | `release_011A_audit_2026-10-15/README.md`, `IMPLEMENTATION_MANIFEST.csv`, inventory, safety matrix, test logs and backup manifest are accessible. Audit manifest contains 340 existing files plus 22 proposed additions, not 362 existing files. |
| OBSERVED NOW | Every one of the 340 current inventoried files matches its Release 011A SHA-256; none is missing. Source ZIP hash also matches. |
| OBSERVED NOW | Read-only SQLite inspection: integrity `ok`, 17 tables, `user_version=0`; current schema and all ordered row values match the consistent backup and restored-check database. |
| OBSERVED NOW | All 340 recovery ZIP members match the backup manifest, and the ZIP archive hash matches. The SQLite backup has different file bytes from the live DB but identical old schema and row values; SQLite backup is not a byte-copy operation. The other 339 members also match the original inventory bytes. |
| AUDIT-RECORDED | Current regression 27/27; current safety 2/24; Release 011 regression 34/34 including seven added tests; Release 011 safety 8/24; both versions' page smoke checks 16/16. Logs were inspected, not rerun in this planning review. |
| OBSERVED EXISTING ARTIFACT | `release_012_safety/` already contains an isolated experimental candidate and evidence recording 84 tests and an external unchanged 24/24 safety run. This is not the operational app, not a fresh execution in this review, and not approval to integrate it. |
| PROPOSED | All repairs, schema additions, test execution, deployment and gate completion described below. |

Current read-only row counts: cases 1; sources 5; requirements 52; compliance 52; CV matches 2; scorecard 10; recommendations 1; risks 6; gaps 11; questions 1; skeleton 3; methodology 2; audit events 36; verification results 0; IP 1; output packages 1; e-GP checklist items 19.

The protected navigation is: Home / Command Center; Workflow Optimizer; Bangladesh e-GP Readiness; Create or Open Case; Upload / Register Inputs; ToR Extraction; Compliance Matrix; CV Matcher; Bid/No-Bid Scorecard; Risk Register and Gaps; Proposal Skeleton and Methodology; Diagnostic Report Generator; Excel Export; IP Capture; Verification / Audit Log; Settings. Preserve each page's existing CRUD/output purpose, not merely its menu label. Keep the current 14 diagnostic report sections plus e-GP readiness and all 16 workbook sheets, including e-GP Readiness.

Supporting documents in this planning folder:

- `SAFETY_CHECK_MAP.csv`: all 24 exact probe names, results, responsible paths, repairs and acceptance evidence.
- `PROPOSED_CHANGE_MANIFEST.csv`: application-relative file targets, rationale, tests and rollback references. It is a proposed delta, not permission to change files.
- `TASK_BOARD.csv`: objectives, dependencies, risks, expected evidence, acceptance and approval checkpoints. Every task is pending and locked.
- `REVIEW_OBSERVATIONS.json`: fresh preservation observations, historical-result classification and explicit authorization state.

## 3. Findings and minimal repair decisions

| Priority | Current code path | Observed issue | Smallest defensible repair |
| --- | --- | --- | --- |
| P0 | `tenderproof/services/bid_score_service.py:54` | Percentage selects positive recommendations without mandatory resolution. | Preserve score arithmetic/thresholds; apply mandatory resolution guard; separate provisional opportunity advice from eligibility and release clearance. |
| P0 | `tenderproof/services/verification_service.py:45` and `:61` | Truthy extraction status and nonempty evidence are insufficient. | Explicit extraction allowlist/coverage review and structured, attributable evidence validity checks. No natural-language string alone proves eligibility. |
| P0 | `source_service.py`, `extraction_service.py:68`, `compliance_service.py:45` | Source, requirement and evidence changes leave clearance usable. | Version inputs, invalidate dependent release state on edits, and re-evaluate a content snapshot at every approval/output boundary. |
| P0 | `case_service.py:70` | Generic updates can assign release labels. | Protect derived readiness and release statuses on creation as well as update; only central policy may promote them. |
| P0 | `workflow_service.py:31` | Any verification rows mean completed. | Require the latest current successful technical run; show explicit approval separately; failed/stale runs cannot complete verification. |
| P0 | `report_service.py:29`, `export_service.py:56` | Output generation trusts cached labels and overwrites prior artifacts. | Preserve draft generation; create versioned artifacts with snapshot/hash/run/approval provenance and enforce current release checks. |
| P1 | `verification_service.py:141` | Artifact existence promotes before warnings are considered. | Blockers first, warnings second, approval/freshness next, artifact prerequisites last. Warning-only results stay PRELIMINARY. |
| P1 | `export_service.py:68` | Client/source strings become Excel formulas. | Store all untrusted textual fields as literal string cells, retaining numeric cells and existing formatting. |
| P1 | `verification_service.py:26`, `ui/tor_extraction.py:58` | Verification history deleted; source quotation overwritten through edit form. | Append verification runs and preserve original quotations; record interpretation edits and supersession instead of destroying provenance. |
| P1 | `db.py`, `tests/conftest.py`, launchers | Unversioned DDL, test filesystem leakage and mutating health check. | Backed-up additive migration journal; isolate all runtime paths; make health check read-only; retain exact launchers and error handling. |

### Release 011 patch disposition

Review only the three-file diff in `release_011A_audit_2026-10-15/release011_changes.patch` and the seven tests under its `isolated/release011/tests/test_release_011.py`.

1. Port the scoring mandatory guard, but **do not equate every Gap with confirmed FAIL**. Missing evidence is UNKNOWN; only an explicit supported negative finding is FAIL.
2. Port `ELIG-001` mandatory/review checks, then route them through the same policy used by reporting and export.
3. Port new-source invalidation, but **do not port deletion of VerificationResult history**. Retain old runs/approvals as historical and superseded.

Public argument signatures in those three files were unchanged by Release 011. Preserve them where practical, adding optional compatible arguments or new helpers only when necessary and covered by call-site tests. Do not copy its entire project: it omits original launchers and configuration. Review the existing experimental Release 012 changes individually against this plan; reuse only justified code and evidence, never wholesale replacement.

## 4. Shared decision contract

Introduce one narrow shared policy helper, proposed as `tenderproof/services/decision_service.py`. Services remain owners of their existing CRUD; the helper evaluates current facts and returns reasons, eligibility, freshness and output authorization. It must not become a second competing workflow engine.

### Eligibility and score semantics

- `PASS`: relevant mandatory criteria have been reviewed and supported by applicable, current, attributable evidence.
- `FAIL`: a reviewed, evidenced mandatory condition is not satisfied. A strategic score cannot override it.
- `UNKNOWN`: missing, ambiguous, placeholder, partial, expired/unvalidated, wrong-entity, contradictory, duplicated or unreviewed support prevents a pass. A missing mandatory set also remains unknown until source coverage and applicability have been established.
- `NOT_APPLICABLE`: requires a reviewed exclusion rationale and provenance. A dropdown alone cannot waive a mandatory criterion.

Preserve existing provisional opportunity scoring. Probe S23 must still allow the synthetic reviewed Met/nonempty row to receive `Pursue` as **provisional score advice**, even though that fixture lacks the new structured evidence and human approval required for release. Never present this result as approved eligibility or a submission authorization.

### Readiness and output state

| Condition | Effective result |
| --- | --- |
| Unknown case, confirmed mandatory failure, explicit unresolved mandatory compliance, or failed/empty/partial relevant extraction | BLOCKED; never positive release clearance |
| Inputs changed after assessment / no assessed snapshot yet | DRAFT_ONLY, or BLOCKED if a current blocker is already known; prior artifacts are historical/stale |
| Nonblocking warnings without blockers | PRELIMINARY, including when a report exists; S17 requires this exact precedence |
| Reviewed legacy Met/nonplaceholder evidence exists, but new structured review/source sign-off has not been completed | PRELIMINARY with explicit release barriers and eligibility UNKNOWN; not evidence PASS and not approvable for release |
| Technical inputs pass but human approval absent | PRELIMINARY; verification may record technical success but cannot grant client readiness |
| Current successful assessment and explicit current approval, but no release report yet | PRELIMINARY / approved-for-generation; no circular requirement to approve an already client-ready report |
| Current approved snapshot and valid generated diagnostic report | CLIENT_READY |
| Same current approved snapshot plus valid report and XLSX package | EXPORT_READY |

Approval is a separate record, not a case status or a positive score. A no-bid diagnostic can be useful and exportable **as an unmistakably BLOCKED/internal-review draft**; it cannot masquerade as positive eligibility clearance. If business later wants formally approved client delivery of a no-bid diagnostic, define a separate delivery-approval policy through explicit scope review, not by weakening mandatory eligibility.

Distinguish diagnostic warnings, technical blockers and release prerequisites in the policy result. S17's reviewed legacy Met row can support a preliminary diagnostic, not a structured evidence pass. Missing the new review records must prevent technical eligibility completion and approval, without converting that warning fixture into BLOCKED solely because a new feature is absent. This compatibility rule is general to legacy draft diagnostics, not a test-specific exemption. An expired/wrong-entity finding or explicitly missing mandatory evidence remains a blocker. Add discriminator tests that first satisfy all other review/approval prerequisites so each negative control proves its own protection, not merely absence of approval.

The release sequence is: review inputs -> technical verification -> human approval of that exact snapshot -> generate approved artifacts -> validate and mark the package. Draft generation remains available before approval. Final content checks are artifact checks, not assessment-input mutations; exclude output records, generated labels and audit bookkeeping from the input fingerprint to avoid self-invalidating cycles.

### Evidence review minimum

Retain existing free-text evidence for continuity, but treat legacy text as unverified for release. Proposed review records identify case/requirement/compliance row, evidence source and actual content hash, bidder legal entity, document identity, issue/expiry dates and relevant period when applicable, applicability rationale, review outcome, reviewer, review time and rationale. Do not invent missing dates or require irrelevant dates for evidence types without expiry.

Use explicit positive and negative review records rather than keyword heuristics. Placeholders cannot count as evidence. Wrong-entity support never satisfies this bidder's criterion; expired support cannot pass a current-validity criterion. Date-limited evidence is evaluated at use time as well as review time. Actual document interpretation remains a human responsibility; generic Release 012 evidence review is not the deferred typed turnover/units/year engine.

### Source versions and amendments

Preserve original uploaded/manual bytes and normalized extraction separately. Store raw/extracted SHA-256, version/supersedes linkage, acquisition time, extraction status, page count/coverage and review disposition. A re-extraction must not silently overwrite the last approved text version. Content hashes detect change, not legal meaning.

New/amended sources default to relevant-unreviewed. The operator must review coverage and affected requirements, update or explicitly supersede affected interpretations, and document any nonrelevance/exclusion rationale before reassessment. Never auto-clear an amendment merely because old requirements still have evidence. Preserve original quotation, match-key behavior and canonical anchors; link changed interpretations to source versions without rewriting historical quotations.

Handle mixed text/scanned PDF pages individually; persist unreadable, truncated, failed or partial coverage and DOCX table text. OCR page caps may remain operational limits but must yield partial coverage and a blocker for relevant unreviewed material. Record human-reviewed exceptions explicitly. No extraction string `failed`, `empty` or `partial` is a successful status just because it is nonempty. Do not claim language/accuracy certification from mocked OCR tests.

### Freshness and invalidation matrix

| Change | Immediate effect | Required re-clearance |
| --- | --- | --- |
| Register/replace/re-extract source or review amendment relevance | Advance case assessment revision; prior approval/output authorization stale | Review active source version and affected requirements; fresh assessment and approval |
| Add/edit requirement, mandatory flag, anchor, interpretation or applicability | Invalidate dependent review/assessment | Review updated criterion and evidence; reassess and reapprove |
| Change compliance/evidence/reviewer disposition or remove evidence | Invalidate release authorization | Current evidence review, verification and approval |
| Edit bidder identity, tender/deadline, CV evidence, score/recommendation or applicable e-GP checklist | Invalidate affected assessment | Re-evaluate current snapshot and obtain approval |
| Change included risks/gaps/questions/skeleton/methodology/IP content | Changed report inputs must not reuse old artifact approval | Re-evaluate fingerprint; reassess/reapprove where included in approved scope |
| External file changes/removal, document expiry or policy version change | Detect at approval/generation/preview/download, even without a UI edit | Deny current-ready access; repair missing/expired inputs and reassess |
| Approval revocation | Revoke future release authorization, preserve history | Fresh explicit approval after technical review |

Use immediate invalidation hooks in existing relevant write services plus a deterministic snapshot as a backstop for UI-level/direct ORM writes. Store canonical snapshot JSON **and** its hash, stable sort order and a policy version. Normalize date/time serialization across SQLite reloads. Exclude only defined nondecision bookkeeping; include all report/decision content actually relied upon. Check eligibility, file hashes, expiry and the current snapshot again at the release boundary; a matching cached revision alone is insufficient.

## 5. Minimal schema and migration proposal

Subject to approval, retain all 17 current tables, every old column and every old row value. Proposed additive design:

| Entity | Proposed addition / responsibility |
| --- | --- |
| Case | Monotonic assessment revision; legacy readiness remains historical/cache, not approval authority. |
| Source | Hashes, versions/supersedes, extraction coverage and attributable scope review. |
| VerificationResult | Optional run linkage; keep existing rows, including legacy unlinked results. |
| OutputPackage | Unique artifact versions with assessment snapshot, verification/approval references, content hash and explicit release state. |
| `evidence_reviews` (new) | Attributable evidence identity, validity, entity and review outcome tied to exact evidence content. |
| `verification_runs` (new) | Immutable serialized inputs/hash, policy version, outcomes, reasons and technical success. |
| `decision_approvals` (new) | Named human, timestamp, rationale, exact successful run/snapshot and revocation history. |
| `schema_migrations` (new) | Applied migration ID/checksum/time and recovery reference. |

Proposed four-table addition would yield 21 tables; this is a design, not a migration applied now. Prefer compatible optional fields and explicit legacy-unreviewed defaults. Never infer human approval from old CLIENT_READY/EXPORT_READY labels. No mass deletion, data reset, destructive table rebuild or automatic logical deduplication is authorized. Existing duplicate demo/question/risk protections remain intact.

Implement explicit SQLite transactional migration in proposed `tenderproof/migrations.py`; back up an existing DB using SQLite's consistent backup API before DDL. Preserve current session rollback/close semantics, use bounded unique-conflict handling/savepoints where necessary, and do not swallow unrelated IntegrityError exceptions. Enforce new relationships where possible without claiming nonexistent legacy foreign keys. Legacy FK/unique table rebuilds require a separately reviewed migration, not hidden scope.

OneDrive is not a database transaction or backup protocol. Select a controlled single-writer maintenance window at eventual deployment, capture WAL/SQLite-consistent state, and retain the backup locally with appropriate access restrictions. No maintenance or server restart is authorized by this planning request.

## 6. Locked task board and milestones

The machine-readable task board supplies source files, changes, risk, evidence, verification and acceptance per task. All tasks remain `pending`, `locked=true`; no task may start until the user approves this plan's implementation scope. The listed dependencies do not imply authorization.

| Task | Priority | Objective / milestone | Dependencies | Human checkpoint |
| --- | --- | --- | --- | --- |
| T00 | p0 | Refresh preservation point; establish isolated reviewed baseline and frozen safety tests | Plan approval | Accept recovery point and exact development target before edits |
| T01 | p0 | Define shared eligibility/freshness policy and backed-up additive migration | T00 | Review policy semantics, schema and migration failure rehearsal |
| T02 | p0 | Port reviewed Release 011 mandatory guards; preserve provisional scoring | T01 | Review FAIL versus UNKNOWN and nonoverride behavior |
| T03 | p0 | Version/review sources and evidence; integrate all relevant invalidation paths | T01 | Review amendment coverage and evidence applicability controls |
| T04 | p0 | Append verification runs; protect case transitions; require explicit approval | T02,T03 | Review local approval identity limits and history |
| T05 | p0 | Gate workflow, reports, workbook and download/preview release boundaries | T04 | Review approved positive flow and blocked/stale artifacts |
| T06 | p1 | Update only necessary existing UI controls, runtime isolation and launch/runbooks | T05 | Founder walks preserved workflows; exact launcher names retained |
| T07 | p0 | Run unchanged safety gates, regressions and data/migration/rollback checks | T02,T03,T04,T05,T06 | Review test definitions and failures without weakening expectations |
| T08 | p1 | Verify all 16 pages and full positive/negative operator workflows | T07 | Human acceptance review of evidence and limitations |
| T09 | p0 | Assemble final diff/evidence/recovery package and merge recommendation | T07,T08 | Separate explicit human merge approval; no automatic deployment |

No estimates of elapsed time or release readiness are asserted. T03/T04 have the largest blast radius; implement and review their smallest dependency-complete increments before moving to outputs.

## 7. Preservation, verification and recovery procedure

### Baseline protection

1. Keep the current 340-file SHA inventory and the full original recovery snapshot immutable. Preserve user files outside the inventory too; exclusions are not deletion permission.
2. On approval, refresh hashes and a consistent database backup before creating an isolated Release 012 working copy. If the live data changed, use the fresh state, not an overwrite from the older audit.
3. Keep the original operational tree unchanged during development. Git is currently uncommitted/untracked; a Git reset is not a valid recovery mechanism. Do not add client data or backups to a source commit.
4. Patch only manifest-approved source paths in the isolated copy. Every changed file requires a rationale, before/after digest, exact diff, related test evidence and original recovery reference. Anything outside the allowlist triggers scope review.
5. Preservation after eventual integration means retained originals and old data, not identical hashes for intentionally approved code patches. During this planning review and isolated engineering, all 340 operational hashes must remain identical.

### Test strategy (future execution, not performed here)

- Freeze all 24 probes exactly as `release_011A_audit_2026-10-15/test_safety_contract.py`, including parameterized cases and both controls. Record its digest and execute that external file against the actual candidate imports. No skip/xfail, test deletion or weakened assertions to obtain green output.
- Preserve/run all original 27 regressions and the seven Release 011 tests. Use all-runtime isolation for SQLite, uploads, extracted text, reports, exports, backups, seed/reference output and temporary OCR images; no test command may write operational storage.
- Add positive evidence-reviewed -> technical-pass -> approval -> MD/DOCX -> XLSX -> download flow. Repeat across committed/reopened SQLite sessions, not only an in-memory transaction. Otherwise a blanket BLOCKED policy could falsely satisfy most safety probes.
- Add specific negatives for expiry at a controlled clock/date boundary, wrong legal entity, placeholder evidence, edited/deleted files, duplicate compliance rows, unjustified N/A, direct readiness assignment at creation/update, absent/revoked/stale approval, amended source re-clearance, unreviewed mixed-PDF pages and failed report parsing. No human approval can override a technical blocker.
- Add invalidation checks for every mutation class in section 4, including direct ORM changes and included report content. Exercise amendment review plus reassessment as a positive recovery path, not permanent blocking.
- Validate MD and DOCX body/tables/headers/footers where supported, label/readiness, complete referenced requirements, timestamp, review footer and all existing sections including e-GP. SAFE-001 must fail closed for required current artifacts that cannot be inspected; retain historical artifacts without letting stale content masquerade as current approval.
- Validate all 16 existing XLSX sheets, header freezing/wrapping, dates, numeric scores and literal text types for `=`, `+`, `-`, `@`-prefixed client/source strings. Test actual stored cell types and read-back text, not only a replacement helper. Apply safe handling to any affected CSV export too without changing unrelated IP semantics.
- Test concurrent amendment versus approval/output generation: recheck snapshot and approval just before commit/publication; abort/quarantine a partial artifact on mismatch. Atomic DB work does not make filesystem publication transactional; test the compensating behavior and preserved historical outputs.
- Rehearse migrations on a fresh DB, historical schema and a restored copy of the real 17-table DB. Compare all original column/value fingerprints, primary IDs, row counts, relationships, source/output paths and artifact hashes. Check integrity, new FK violations where applicable, second-run idempotence and failure injection before commit.
- Restore the pre-migration backup and confirm old schema/values plus source/output readability. A zero-result foreign-key check does not establish enforcement for old tables that declare no FKs.
- Run Streamlit AppTest for all 16 pages, then actual browser interactions at desktop and narrow viewport: upload/manual intake, edit/review, evidence, scoring, approval, draft/report/workbook generation, stale denial, history and downloads. Record exceptions and artifact readability, not just page titles.
- Exercise both exact Windows launcher paths with spaces and `&`, default `run_app.py` invocation and every documented flag. Make `--check` read-only. Verify clean dependency installation for each Python version actually claimed; retain the tested environment snapshot and add a compatible lock/constraints artifact rather than silently upgrading the live environment.

Proposed command shape, **only after approval and runtime isolation**: run the candidate interpreter with `-B -m pytest tests -q --junitxml=<isolated-evidence-path>`, then the frozen external safety file in a separate pytest process with candidate import root and isolated runtime paths. Record exact resolved interpreter, cwd, environment variable names (not secrets), exit code, passed/failed/skipped counts and input hashes. Do not run current `run_app.py --check` on the operational database: it presently initializes data.

### Rollback references and deployment checkpoint

R0: original inventory `release_011A_audit_2026-10-15/source_inventory_before.json` and matching source/asset members in `backup/project_snapshot.zip`.
R1: consistent `backup/storage/tenderproof.db`, restore-check DB and `backup_manifest.json`; use schema/row equivalence for SQLite, not an assumed byte-identical backup.
R2: **future required** fresh pre-implementation and pre-deployment snapshots, hash manifests and tested restore logs reflecting any newer user data.

After separate merge approval, stop only the affected app worker for the maintenance window, take R2, apply the reviewed allowlisted diff and migrate with its journal. Start a fresh worker, exercise the synthetic smoke path without touching client records, and confirm operational paths/labels. Do not replace current data with candidate/demo storage. If a gate fails, preserve the failed/new state before any switch, validate a matching source/database recovery pair in a separate directory, and obtain the authorized recovery decision. Do not blindly roll back the DB and discard newer records. Account for absolute stored Windows paths; a tested explicit remapping is required for a relocated restore.

## 8. Evidence ledger

| Ref | Type / status | Observed result or future required evidence | Location |
| --- | --- | --- | --- |
| E01 | observation / collected now | 340/340 current hashes match; source ZIP unchanged | Original `source_inventory_before.json`; this folder's `REVIEW_OBSERVATIONS.json` |
| E02 | observation / collected now | DB read-only integrity ok; 17 schemas/ordered row sets equal backup and restore check | `tenderproof_os/storage/tenderproof.db`; audit `backup/storage/tenderproof.db`, `backup/restore_check.db` |
| E03 | observation / collected now | 340/340 backup members and archive digest match backup manifest | Audit `backup_manifest.json`, `backup/project_snapshot.zip` |
| E04 | test_result / historical inspected | Current 27/27 regression, 2/24 safety; 011 34/34 regression, 8/24 safety | Audit `test_results/summary.json`, `SAFETY_TEST_MATRIX.csv`, JUnit/logs |
| E05 | test_result / historical inspected | Both audited versions 16/16 AppTest pages; limited smoke coverage | Audit `test_results/current_ui.json`, `release011_ui.json` |
| E06 | artifact / historical inspected | Three-file reviewed 011 diff and unchanged public argument signatures | Audit `release011_changes.patch`, `api_compatibility.json` |
| E07 | test_result / existing candidate only | Prior isolated 012 summary records 84 tests and external 24/24; not rerun or accepted as this plan's release gate | `release_012_safety/evidence/verification_summary.json` |
| E08 | artifact / produced now | Plan, 24-row map, proposed file delta, locked tasks and fresh observations | This planning folder only |
| E09 | test_result / NOT YET COLLECTED | Fresh approved-candidate regressions, unchanged safety, positive flows, UI/browser and launch evidence | Proposed isolated Release 012 evidence directory, T07/T08 |
| E10 | artifact / NOT YET COLLECTED | Per-file diff/rationale, migration journal, actual-data fingerprint comparison and restore rehearsal | T00/T01/T07/T09 |
| E11 | human_note / NOT YET COLLECTED | Explicit plan implementation approval, later acceptance and separate merge authorization | User approval record identifying this plan revision and candidate digest |

Sensitive case/evidence content in snapshots, reports and logs stays local under the owner's controls. Share sanitized evidence only; do not publish client files or credentials.

## 9. Verification dashboard

All Release 012 acceptance gates below remain `pending` for this approval-controlled plan. Observed baseline preservation is not permission to mark the future integration accepted. No gate has a bypass; any proposed exception requires an explicit authorized rationale, with mandatory safety failures still blocking release.

| Gate | Task | Pass criteria | Required evidence | Status / resolver |
| --- | --- | --- | --- | --- |
| G01 Safety contract | T02-T05,T07 | Exactly all 24 unchanged probes pass, zero hidden skips/xfails | Frozen test hash, external execution log/JUnit and S01-S24 mapping | pending / engineering reviewer |
| G02 Regression | T07 | Original 27 plus seven 011 tests and new focused/positive tests pass | JUnit, exact commands, no removed/weakened assertions | pending / QA reviewer |
| G03 Mandatory nonoverride | T02,T04,T07 | FAIL and unresolved mandatory criteria cannot yield positive clearance at any score; S23 provisional control preserved | Negative parameterized plus distinct approved-positive tests | pending / product + safety reviewer |
| G04 Evidence controls | T03,T07 | Identity/provenance/completeness/entity/expiry and explicit UNKNOWN/FAIL states enforced | Structured review, date-boundary and physical-file tamper/removal tests | pending / evidence reviewer |
| G05 Amendment/freshness | T03-T05,T07 | Relevant amendments and all dependent edits invalidate approvals; old assessment cannot reclear them | Version/snapshot/history and amendment review recovery tests | pending / engineering reviewer |
| G06 Release boundary | T04,T05,T07 | Unapproved, revoked, stale or changed artifacts cannot be currently client/export-ready; literal spreadsheet text | Approval, race/recheck, DOCX/MD/XLSX read-back, preview/download tests | pending / QA + human approver |
| G07 Existing UX | T06,T08 | All 16 pages render; preserved end-to-end workflows and both launchers function | AppTest + actual browser/operator runbook and Windows launch logs | pending / Syful or named operator |
| G08 Preservation/recovery | T00,T01,T07 | Original 340 operational hashes unchanged during isolated work; additive real-copy migration preserves old data; failure rollback and restore demonstrated | Inventories, full old-value fingerprints, integrity/relationship checks, recovery logs | pending / owner + engineering reviewer |
| G09 Approval governance | T09 | Gates G01-G08 pass and exact reviewed diff/recovery point receive explicit merge approval | Signed/named approval record with plan revision and artifact digests | pending / Syful |

Approval of the engineering plan is not G09 and is not approval of a tender bid. These are three distinct decisions: implement this repair scope; merge a verified software candidate; approve a particular case's evidence snapshot inside the app.

## 10. Approval checkpoint and safe next action

Plan preparation and read-only review are complete. **Implementation and merge remain pending your approval.** The existing isolated candidate is preserved but has no implied authorization.

Approval should identify this plan revision and authorize only T00-T08 in an isolated working copy, plus T09 evidence preparation. It must not authorize modification of `tenderproof_os/`, a live migration, release approval or e-GP expansion. A later explicit merge decision follows the fresh evidence package.

Safe next action: Syful reviews the policy distinctions, 24-check map, proposed file scope and recovery procedure, then approves, rejects or requests changes to this plan. Until then, the task board remains locked and the operational application remains untouched.
