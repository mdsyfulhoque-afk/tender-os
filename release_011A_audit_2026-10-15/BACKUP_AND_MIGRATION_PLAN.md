# Proposal Guard Backup and Migration Plan

The Release 011A audit produced a verified preservation snapshot before running application code in isolated copies. The operational application is unchanged. This plan governs the later Release 012 integration and additive e-GP development.

## Existing recovery evidence

`backup/project_snapshot.zip` contains the inventoried application source, documentation, configuration, launchers, seed/reference files and saved storage. Its database member is a transactionally consistent SQLite backup created from a read-only source connection. Runtime dependencies, Git internals, caches and temporary rendering images are excluded explicitly in `backup_manifest.json`.

Every ZIP member was read back and compared with its SHA-256 digest. The database was then restored to `backup/restore_check.db`; SQLite integrity and row counts for every table matched the original snapshot. `backup/storage/tenderproof.db` is the standalone consistent database backup. These local files contain the saved case data and should remain with the project owner's controlled backups.

`file_inventory.csv` and `source_inventory_before.json` record 340 operational file hashes. `preservation_check.json` records the final comparison. The source ZIP fingerprint also matches the prior 14 October baseline evidence. Source Markdown/DOCX references are preserved under `references/` with `reference_hashes.json`.

## Restore rehearsal

Restore into a new directory so that the original and historical audit evidence remain available. Use a Python installation to extract this audit-produced snapshot and recreate a virtual environment. The captured environment is Windows Python 3.14.5; `requirements.environment_snapshot.txt` records installed package versions, not a cross-platform lock guarantee.

Example PowerShell, from this audit directory:

```powershell
$restore = Join-Path $env:TEMP ('ProposalGuard_Restore_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $restore | Out-Null
& '..\tenderproof_os\.venv\Scripts\python.exe' -m zipfile -e '.\backup\project_snapshot.zip' $restore
```

Confirm the restored ZIP member hashes and the restored database's table counts against `backup_manifest.json` and `database_schema.json`. Before allowing the restored app to use client data, verify that Source and OutputPackage paths still resolve. Current stored paths are absolute Windows paths; moving the application to another directory requires an explicit, tested path-remapping plan. The snapshot's successful SQLite restore check does not by itself prove portability of those external path references.

Do not restore over operational storage as a routine test. A deliberate production recovery should first capture the newer operational state and identify the intended recovery point.

## Release 012 integration sequence

1. Establish a reviewed source baseline and development branch or separate copy. Git currently has no commits; retain this snapshot independently of Git.
2. Record current source, database and document hashes. Verify that the database is not actively changing while selecting the migration recovery point.
3. Make a fresh SQLite backup and restore it into the migration test environment. Retain the entire source/storage snapshot.
4. Integrate only the reviewed service changes and regression checks from Release 011. Keep the two Windows launchers, `.streamlit/config.toml`, reference assets and all old workflows.
5. Add a migration journal and new evidence/version/approval tables using additive DDL. Backfill new optional fields without reinterpreting old readiness labels as approved decisions.
6. Run the migration on the restored real database. Compare pre-existing row counts, keys, source hashes, old values, output paths and original artifacts; run integrity and orphan-link checks.
7. Exercise the migration twice to confirm idempotence. Inject a failure before commit and verify rollback. Check a fresh empty database and the historical schema shape as well.
8. Run original regressions, the completed safety contract, all 16 page checks, report/export regressions and the synthetic end-to-end tender assessment. Isolate filesystem output as well as SQLite.
9. Prepare the reviewed release diff, backup reference, environment constraints, recovery commands and verification evidence before the deployment decision.

## Additive schema rules

Retain existing tables, columns, case IDs and original documents. Add source/evidence versions and link immutable assessment snapshots to their exact input hashes and reviewer decisions. Preserve old verification/approval records and mark them superseded instead of deleting them.

Introduce foreign keys and logical uniqueness only after auditing existing duplicate/orphan conditions and testing migration compatibility. Adding constraints to SQLite may require a table rebuild; do not silently perform one as an allegedly additive column operation. Such a step needs its own preservation and rollback verification.

Keep source registration, requirement edits, compliance/evidence changes, approval and report/export decisions synchronized through a shared policy. A high opportunity score never supplies mandatory evidence. UNKNOWN, unreviewed or missing input must not become PASS. An old approval cannot authorize an output after a dependent source or evidence version changes.

## Rollback verification

Run migration and application checks against copies before release. For a production rollback, stop the affected app worker, retain a fresh backup of its current state, and restore a matching source/database pair to a separate location for verification. Verify original document/output paths and the selected recovery point before any intentional switch of the operational directory.

Recovering from a database snapshot can lose records created after that snapshot. Prefer reversible additive migrations that permit the previous application to continue reading old data; avoid deleting newly collected records during rollback. The restore rehearsal here confirms the audit backup's integrity, not an untested future migration.
