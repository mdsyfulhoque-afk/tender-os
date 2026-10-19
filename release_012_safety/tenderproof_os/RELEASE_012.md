# Proposal Guard Release 012 Safety Integration

This is the isolated Release 012 review candidate. The original application and its saved database remain in the parent workspace's `tenderproof_os` folder. Merging or replacing that application requires the user's separate merge authorization.

## Operator workflow

1. Create or open a case; register the tender and supporting documents.
2. Extract or add source-linked requirements. Review each mandatory clause in ToR Extraction and clear Needs review only after checking the source quotation and current interpretation.
3. Map compliance and enter actual evidence. Missing, partial, unknown or unjustified Not Applicable rows cannot supply mandatory clearance.
4. In Verification / Audit Log, record each current source review and explicitly confirm complete applicable clause coverage.
5. Record evidence reviews with the bidder's legal entity, supporting source or attachment, validity dates or an explicit non-expiry reason, reviewer and rationale. An unresolved evidence row remains unresolved.
6. Complete the opportunity scorecard and applicable e-GP checklist. Opportunity scores do not override mandatory eligibility.
7. Run verification after the latest reviews and changes. Approval is available only when all technical checks pass for that exact source/evidence snapshot.
8. A named human records approval of the current snapshot. Generate a new approved report, then the approved Excel package. Draft outputs remain available when clearance is pending or blocked.

## Safety behavior

Every relevant input contributes to the assessment fingerprint, including current document and attachment bytes. Source, requirement, compliance, evidence, case and checklist changes invalidate previous clearance. Physical file changes, removed attachments and expiry also block release when the policy is evaluated. Validity dates use Asia/Dhaka calendar dates; stored event timestamps use UTC.

Verification runs retain their complete serialized input snapshots and rule results. Approvals reference an exact successful run and snapshot. Evidence attachments reviewed directly by file path are also archived, while the original path remains monitored for subsequent changes. Reports and workbooks use unique filenames and include source, evidence, review and approval references; historical files are retained.

The single-workstation trust boundary is unchanged: the operator supplies a reviewer identity and explicitly approves in the local UI. There is no new multi-tenant identity system, remote approval API or public deployment. Procurement authenticity and whether a document substantively proves a clause still require professional review; the typed financial/company qualification engine belongs to the later e-GP releases.

## Database and recovery

Initialization performs migration `012_safety_1` in an explicit SQLite transaction. It preserves the existing 17 tables and original fields, adds review/hash/version fields, and adds evidence_reviews, verification_runs, decision_approvals and schema_migrations. Existing nonempty databases receive a consistent backup in the database's adjacent backups folder before the first migration. A second initialization is idempotent.

Existing legacy rows are not silently certified or approved. They remain available for review. Absolute paths in old source/output records are retained; use the isolated synthetic preview for evaluation. Copying client storage to a different directory requires a deliberate path migration and its own verification.

The evidence directory outside this application contains the real-data migration, restore and preservation checks. No application migration was run on the original operational database.

## Verification and preview

From the enclosing `release_012_safety` folder, double-click `preview_release_012.bat`. It uses the already verified Python environment and the separate `preview` storage root. The preferred URL is `http://localhost:8512`; an occupied port causes the launcher to select a nearby free port and print the actual URL.

The two original application launcher filenames remain present. The candidate's tests isolate output files and databases from operational storage. `python run_app.py --check` is now a read-only import/database-integrity check; `--init-db` performs initialization and migration explicitly.

The unchanged 24-check safety contract is in `tests/test_release_012_safety_contract.py`. The seven reviewed Release 011 probes are retained in `tests/test_release_011.py`. Additional tests prove a successful review/approval/report/export workflow, cross-session snapshot stability, mutations, expiry, revocation, immutable source/evidence history, migration rollback and UI approval confirmation.
