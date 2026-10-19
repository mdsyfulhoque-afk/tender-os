# Recovery and integration review

Merge authorization: pending_approval. This document authorizes no operational changes.

## Preserved recovery point

The engineering baseline is baseline/project_snapshot.zip plus baseline/tenderproof.db. evidence/baseline.json records its inventory and recovery information. These local files contain client records; they are excluded from the code-review ZIP.

The resumption compared baseline-file digests before and after restoration and verification. Neither these snapshots nor the operational 340-file inventory was modified. Historical Release 011A backups remain separate.

## Executed recovery procedure

The recovery runner copies the baseline DB into evidence/recovery/ and migrates that copy only. It compares every original column/value set across all 17 old tables, checks integrity and new foreign-key violations, repeats initialization for byte-level idempotence, and restores the automatic pre-migration backup into another separate file.

The restored copy is compared with the original tables, columns and old values. See evidence/recovery.json. Legacy tables have no declared foreign keys; a zero-result foreign-key check does not imply retroactive constraint enforcement.

Fresh regressions also exercise injected transactional migration failure. evidence/transactions.json records a separate synthetic unique-conflict rollback, preserved baseline record and healthy subsequent session.

## Required future integration decision

The owner reviews:

1. Exact candidate/code-package digests, per-file rationale, source digests and fresh test records.
2. All 24 protected checks, including S17 warning precedence and S23 provisional scoring.
3. Approved output read-back and stale/blocked release denial.
4. Recovery evidence, operator workflow and limitations.
5. R012-N01: audit report text uses staging filenames while authoritative output records identify final verified files.

Human verification gates remain pending until explicitly resolved. Merge approval and individual tender-case approval are different decisions.

## Future safeguards

Only after separate explicit authorization: refresh operational inventory and a consistent backup to protect newer data; select a single-writer maintenance window; apply the reviewed allowlist; migrate current data through the tested journal. Never replace storage with candidate or QA storage.

For recovery, preserve the failed/new state first and validate a matching source/database pair in a separate directory. Blind old-DB restoration could discard newer cases and is not authorized. Absolute stored paths require tested remapping if moved.

This run neither performs nor pre-approves those future steps.
