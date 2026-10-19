# Release 012 isolated operator review

This is a review candidate, not the operational installation. Merge remains pending_approval. Results apply only to this candidate and its synthetic test runtimes.

Workspace: C:\Users\IP3 Consulting Ltd\OneDrive\Documents\Proposal Guard

Candidate: release_012_controlled_2026-10-15\tenderproof_os

## Safe review

Do not replace the operational tenderproof_os, copy a QA database into it, or migrate it. Do not copy the development tree wholesale. Operational safety findings remain until a separately approved integration.

The code-review ZIP contains changed files only, not a standalone installation. Its raw member bytes and CHANGE_MANIFEST.csv digests are authoritative. The text patch is for review, not authoritative for CRLF-sensitive protected tests.

## Optional later human review

No test server is intended to remain running after verification. To review later, use a new synthetic runtime rather than the copied legacy DB. From PowerShell:

~~~powershell
$root = 'C:\Users\IP3 Consulting Ltd\OneDrive\Documents\Proposal Guard\release_012_controlled_2026-10-15'
$env:TENDERPROOF_RUNTIME_ROOT = Join-Path $root 'runtime\operator_review'
$env:TENDERPROOF_DB_PATH = $null
& (Join-Path $root 'tenderproof_os\.venv\Scripts\python.exe') (Join-Path $root 'tenderproof_os\run_app.py') --run --port 8530
~~~

Read the actual printed URL if the preferred port is occupied. Stop its terminal process when finished. This is local review, not authorization for integration or public deployment.

Both exact launchers remain: deploy&run.bat and deploy_and_run.bat. To invoke either normal launcher for human review, set the isolated runtime above first and call its quoted path. The primary can install dependencies and run tests; it is not read-only. Never point its runtime at operational storage.

## Review workflow

1. Create/open a synthetic case and register ToR text or documents.
2. Review requirements, original quotations, anchors and mandatory status.
3. Map compliance; provide actual synthetic evidence or leave Gap/Pending Input. Confirm CV evidence and complete opportunity scoring.
4. In Verification / Audit Log, review active source versions and clause coverage.
5. Record evidence identity, bidder entity, applicable validity and named review. Register supporting documents as distinct sources when using the UI. Not Applicable requires an attributable source-based exclusion.
6. Run verification. Provisional Pursue is not evidence PASS or release authorization.
7. For a technically valid current snapshot, use explicit human confirmation and approval. Synthetic QA approvals are not real tender endorsements.
8. Generate MD/DOCX and XLSX; inspect readiness, snapshot, approval and gaps. The workbook retains all 16 sheets.
9. Change a relevant requirement/source/evidence input; confirm old approved output is stale and cannot appear currently approved.
10. Inspect run/approval history without deleting previous records.

Warnings stay PRELIMINARY. Strategic scores and approval attempts cannot override mandatory blockers. A useful blocked diagnostic remains available only as a clearly blocked draft.

## Limits

Named local review is an operator audit record, not multi-user authentication. No portal automation/submission, external AI, full numeric qualification engine or OCR language accuracy certification is included. Experts must establish whether actual documents prove real tender criteria.

Visiting the existing e-GP page activates its checklist; pending applicable items invalidate clearance. Recorded browser verification used the negative synthetic case for that page to preserve the approved fixture.

The application's README/QUICKSTART remain baseline files during this verification-only resumption. Use this review runbook for the new controls; documentation integration is part of the separate release decision.
