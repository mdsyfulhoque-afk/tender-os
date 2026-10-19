# Release 012 controlled implementation: stopped at frozen-test checkpoint

Status: **STOPPED / verification incomplete / not release-ready**.
Implementation approval covers isolated work only. Merge and deployment remain `pending_approval` / not authorized. No human verification gate has been approved by automation.

## Preservation

All 340 operational files still match the original inventory. No missing or unexpected operational files were found, and the original source ZIP digest still matches. No operational database migration, application modification, server restart or deployment was performed.

The new development copy was created from the verified current application, not by wholesale copying the experimental candidate. Selected individual repairs were recorded in `evidence/selective_port_ledger.json`. A fresh recovery snapshot and consistent database backup are under `baseline/`; their digests and baseline schema/row values are recorded in `evidence/baseline.json`.

## Checkpoint finding

The fresh-environment verification harness stopped before executing its final regression/external-safety phases because the supplementary seven-test Release 011 copy was not byte-identical to its reference:

| File | Reference SHA-256 | Candidate SHA-256 |
| --- | --- | --- |
| `tests/test_release_011.py` | `886027e6f63f2f8e68b1bce330acdb3687ca47e9a4b955c4d253f20ce3bdbd7e` | `dd7cb078f4287ca061e4aa7b1ebb10b7bdf30045e0ca3e19c171889c9a264b6c` |

Read-only diagnosis: the reference is 3,647 bytes with 123 CRLF sequences; the newly added copy is 3,524 bytes with LF line endings. Normalizing line endings makes the contents exactly equal. No test code, expected outcome or assertion differs. This arose while porting the individual file through the patch tool. The isolated copy has not been silently corrected after the checkpoint.

**The required 24 original safety probes ARE byte-identical**, including S17 and S23: both digests are `e95747e2ba52edc138e333e9a3cc3e2c41a7cb043d454e8e2eeefde00186c00a`. All 11 pre-existing test modules also retain their original hashes; only the explicitly approved runtime-isolation fixture was changed.

## Work implemented before stop

- Shared current-input policy; distinct provisional scores and verified release authority.
- FAIL / UNKNOWN / PASS and reviewed NOT_APPLICABLE handling; no score override of mandatory conditions.
- Structured source/evidence review, source hashes/versions and coverage metadata, evidence identity/entity/validity and physical file checks.
- Snapshot-bound named local approval, revocation, append-only verification snapshots/history and protected case release fields.
- Versioned MD/DOCX/XLSX output, report safety inspection including DOCX tables/headers/footers, final approval/freshness recheck under a SQLite write boundary, and quarantine on publication failure.
- Literal Excel text, guarded IP CSV text, preserved report/workbook/page structures, and existing-page review/approval controls.
- Backed-up additive migration journal/checksum/recovery references; isolated runtime paths; read-only health check; compatible dependency constraints and retained Windows launcher names.

These are implementation observations, not a claim that the final candidate is accepted. See the current diff and per-file manifest.

## Executed evidence

| Execution | Observed result | Limit |
| --- | --- | --- |
| Initial isolated suite | 84 passed, zero failures | Used the original installed interpreter without altering that environment; included 24 safety probes, seven Release 011 checks, original regressions and previous candidate coverage. |
| New discriminator tests | 36 passed, zero failures | Exercised approved-case invalidation, reviewed exclusions, distinct outcomes, amendment recovery, revocation during MD/DOCX/XLSX generation, report inspection, formulas and mixed-source coverage. |
| Clean candidate virtual environment | Requirements installed successfully using the recorded constraints | Separate `.venv`; operational dependencies unchanged. Windows Python 3.14 only; no other Python compatibility claim. |
| Protected-test preflight | Stopped on the seven-test file byte mismatch | Final fresh-environment combined suite and separate external 24-probe execution did not begin. |
| Preservation/features inspection | 340 operational hashes match; original navigation, sheets, report sections and copied data/assets retained | Static inspection is not browser or operator acceptance. |

One subsequently added IP CSV test has not been executed. The final candidate has not received a completed fresh combined suite, separate external-safety execution, dedicated actual-data migration/restore rehearsal, 16-page interactive/browser acceptance or real launcher acceptance. Earlier passing tests are not substituted for these missing steps.

## Outstanding issue and recovery

Issue R012-STOP-001: frozen supplementary test bytes differ by line endings. Proposed recovery is an exact binary recopy of **only the isolated** `tests/test_release_011.py` from its audited reference, followed by digest comparison. Do not alter assertions, normalize the reference, weaken the guard or touch operational files. This correction has not been performed after the stop.

After an explicit resume instruction, complete the frozen-test check, fresh combined/external safety runs, pending CSV check, dedicated recovery rehearsal, all 16 UI/browser workflows, launcher verification and final evidence reconciliation. Any mandatory failure remains a stop condition. No merge or deployment follows automatically.

The current code-review ZIP excludes client storage and databases. Do not apply it to the operational app. The full baseline is retained separately for local recovery. Preserve both the current incomplete candidate and its logs so the stop is auditable.
