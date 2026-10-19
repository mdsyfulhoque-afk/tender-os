"""Generate file dispositions and acceptance coverage from collected audit evidence."""

import csv
import hashlib
import json
from pathlib import Path
import re


OUT = Path(__file__).resolve().parent

CHANGES = {
    "app.py": ("EXTEND", "013-015", "Retain all 16 pages and add the e-GP workflow within this application.", "Existing navigation and isolated page smoke checks remain green."),
    "run_app.py": ("EXTEND", "012", "Separate read-only health checks from initialization; support isolated data roots and migration checks.", "Check mode leaves an existing database byte-for-byte unchanged."),
    "requirements.txt": ("EXTEND", "012", "Retain the stack; add a tested environment lock and explicit OCR model configuration.", "Clean Windows environment installs the pinned tested set and passes pip check."),
    "README.md": ("EXTEND", "012-017", "Document eligibility versus attractiveness, approval gates, current 16 workbook sheets, and staged scope.", "Runbook matches the tested commands and actual artifact counts."),
    "QUICKSTART.md": ("EXTEND", "012", "Document backup, fresh worker restart, draft outputs, review and approval.", "Founder can complete a synthetic assessment with the revised gates."),
    "deploy&run.bat": ("EXTEND", "012", "Keep the exact launcher name; pin installation and isolate tests from operational storage.", "Double-click launch succeeds without adding test files to operational storage."),
    "deploy_and_run.bat": ("KEEP", "012", "Preserve the quoted ampersand-safe wrapper.", "Wrapper continues to call the exact primary launcher."),
    "tenderproof/config.py": ("EXTEND", "012", "Preserve REFERENCE_DIR and add one explicit configurable data/storage root.", "All test and runtime paths stay within the selected root."),
    "tenderproof/db.py": ("EXTEND", "012", "Retain session rollback and add versioned additive migrations with backup and rollback checks.", "A restored real schema migrates without losing rows; failed migration rolls back."),
    "tenderproof/models.py": ("EXTEND", "012-015", "Preserve 17 tables; add source versions, verified evidence, assessment snapshots and human approval records, then linked e-GP profiles.", "Old rows and identifiers survive; new relationships and constraints pass compatibility tests."),
    "tenderproof/schemas.py": ("EXTEND", "012-014", "Add explicit PASS, FAIL, UNKNOWN, review, provenance and snapshot schemas.", "Unknown and missing evidence cannot coerce to a verified pass."),
    "tenderproof/constants.py": ("EXTEND", "012", "Keep existing display values while adding separate eligibility and approval state vocabularies.", "Original score threshold tests remain valid; eligibility overrides final clearance."),
    "tenderproof/services/bid_score_service.py": ("REPAIR", "012", "Integrate the reviewed Release 011 guard; separate opportunity percentage from final eligibility and clearance.", "Mandatory failed, missing, duplicate, unreviewed and N/A-without-reason states prevent positive clearance."),
    "tenderproof/services/verification_service.py": ("REPAIR", "012", "Integrate ELIG-001, fail closed on incomplete evidence/extraction, check snapshot freshness, retain historical runs, and honor warning precedence.", "Safety probes pass for stale sources, invalid evidence, unresolved checks, warnings and missing approval."),
    "tenderproof/services/source_service.py": ("EXTEND", "012", "Integrate source invalidation; add SHA-256, source versions and processing coverage, preserving verification history.", "Amendment cannot regain clearance until new requirements and dependent evidence are reviewed."),
    "tenderproof/services/workflow_service.py": ("REPAIR", "012", "Compute completion from current successful verification and approval, rather than record counts.", "Failed or stale verification never marks verification complete."),
    "tenderproof/services/report_service.py": ("REPAIR", "012/016", "Recompute release eligibility, version artifacts and include evidence, source and reviewer snapshots; retain existing report sections.", "Evidence removal prevents stale client-ready labels and old outputs remain auditable."),
    "tenderproof/services/export_service.py": ("REPAIR", "012/016", "Apply the shared release gate and store untrusted spreadsheet text as literal strings; retain all 16 sheets.", "Formula text remains text; missing approval or freshness permits draft output only."),
    "tenderproof/services/case_service.py": ("REPAIR", "012", "Protect readiness and release statuses behind authoritative transition validation.", "Generic case create/update cannot self-assign CLIENT_READY or EXPORT_READY."),
    "tenderproof/services/extraction_service.py": ("REPAIR", "012/014", "Invalidate dependent checks after requirement edits; retain source quotations and record reviewed changes.", "Editing a threshold invalidates the previous assessment and preserves its original quotation."),
    "tenderproof/services/compliance_service.py": ("REPAIR", "012", "Invalidate assessments after evidence/status edits and enforce one current compliance row per requirement.", "Removing evidence invalidates readiness and the related historical approval cannot authorize new outputs."),
    "tenderproof/services/tor_normalizer.py": ("EXTEND", "014", "Preserve original text, real page/section provenance, units and uncertainty; retain deterministic keys.", "Bangla, mixed text, numeric units and repeated clauses are reviewed with source-linked fixtures."),
    "tenderproof/services/gap_service.py": ("EXTEND", "012/015", "Keep idempotent gap synchronization and link gap severity/status to current assessments.", "Resolved and reopened gaps track evidence changes without duplicate active items."),
    "tenderproof/services/risk_service.py": ("EXTEND", "012/015", "Preserve duplicate prevention and use explicit requirement/gap severity in verification.", "High and critical gaps missing risk entries are detected even when gap_type is compliance."),
    "tenderproof/services/cv_match_service.py": ("EXTEND", "014", "Keep evidence-only drafting and add verified source links, entity/context and expiry checks as applicable.", "Provided text alone is never treated as proof that a mandatory criterion was verified."),
    "tenderproof/services/audit_service.py": ("EXTEND", "012", "Keep existing events and add reviewer, snapshot version and immutable decision event details.", "Amendment and review events preserve old evidence and approval provenance."),
    "tenderproof/services/egp_service.py": ("EXTEND", "013-015", "Preserve the 19-item checklist; link applicable items to tender-specific assessment and justified exclusions.", "Pending applicable checklist items appear as readiness blockers."),
    "tenderproof/ui/cases.py": ("REPAIR", "012", "Preserve case editing and route release status changes through reviewed transitions.", "UI cannot manually claim a released status without the service-level gate."),
    "tenderproof/ui/tor_extraction.py": ("REPAIR", "012/014", "Retain manual editing while keeping immutable source text and explicit review actions.", "Editing interpretations does not overwrite the original ToR quotation."),
    "tenderproof/ui/bid_scorecard.py": ("EXTEND", "012", "Display opportunity score, eligibility result, pending evidence and approval separately.", "A high score with mandatory failure visibly remains blocked."),
    "tenderproof/ui/verification.py": ("EXTEND", "012", "Show current versus stale runs and attributable human review/approval.", "Historical runs remain visible without conferring current clearance."),
    "tenderproof/ui/report_generator.py": ("EXTEND", "012/016", "Retain Markdown and DOCX creation/download while presenting draft and approved versions accurately.", "Only current approved snapshots can be presented as approved deliverables."),
    "tenderproof/ui/exports.py": ("EXTEND", "012/016", "Preserve workbook generation; add file download and accurate release labels.", "Founder can download the workbook with its current approval state."),
    "tenderproof/ui/egp_readiness.py": ("EXTEND", "013-015", "Keep existing checklist/reference view and connect the integrated Tender-to-Fit workspace.", "Existing 19 checks and guide download remain available."),
    "tenderproof/ui/intake.py": ("EXTEND", "012-014", "Retain upload/manual text/OCR progress; show processing completeness, version changes and review state.", "Unreadable, truncated or partly processed material cannot appear fully verified."),
    "tenderproof/ui/workflow_optimizer.py": ("EXTEND", "012/015", "Keep next-step navigation and surface eligibility, freshness and reviewer blockers.", "Failed verification directs the operator to unresolved work."),
    "tenderproof/ui/settings.py": ("EXTEND", "012", "Retain initialization and demo controls; add explicit backup/restore and migration status.", "Existing data is protected by the verified snapshot and additive migration path."),
    "tests/conftest.py": ("EXTEND", "012", "Retain temporary databases and isolate all filesystem output as well.", "Running the full test suite leaves operational storage unchanged."),
    "tenderproof/prompts/egp_document_review.md": ("EXTEND", "016", "Retain evidence safeguards and add typed clauses, page citations, uncertainty and review schema.", "Prompt output cannot directly approve mandatory eligibility."),
}

ADDITIONS = {
    "tenderproof/services/approval_service.py": ("012", "Attributable local human approval bound to an immutable assessment snapshot."),
    "tenderproof/services/decision_service.py": ("012", "One shared eligibility, freshness and release policy consumed by existing services."),
    "tenderproof/migrations/__init__.py": ("012", "Versioned additive migration runner following existing SQLAlchemy architecture."),
    "tenderproof/services/egp/__init__.py": ("013", "Integrated feature domain within Proposal Guard."),
    "tenderproof/services/egp/tender_intake_service.py": ("013", "Manual official-document intake and tender identifiers linked to cases/sources."),
    "tenderproof/services/egp/tender_document_service.py": ("013", "Document provenance, source versions and processing coverage."),
    "tenderproof/services/egp/company_profile_service.py": ("013", "Company legal entity, qualifications and supporting evidence vault."),
    "tenderproof/services/egp/qualification_service.py": ("014", "Deterministic numeric, temporal, categorical and document qualification rules."),
    "tenderproof/services/egp/tender_matching_service.py": ("015", "Company fit ranking subordinate to mandatory eligibility."),
    "tenderproof/services/egp/bid_readiness_service.py": ("015", "Tasks, deadlines, required forms and bid preparation readiness."),
    "tenderproof/services/egp/amendment_service.py": ("012/017", "Manual amendment invalidation first, authorized monitoring later."),
    "tenderproof/ui/egp_tenders.py": ("013", "Tender intake integrated into the existing page navigation."),
    "tenderproof/ui/company_profiles.py": ("013", "Reusable verified company qualifications."),
    "tenderproof/ui/egp_assessment.py": ("014", "Source-linked requirement and eligibility review."),
    "tenderproof/ui/bid_readiness.py": ("015", "Company-specific readiness tasks and ranking."),
    "tests/test_release_011.py": ("012", "Preserve candidate regression probes while completing the broader safety contract."),
    "tests/test_approval_and_freshness.py": ("012", "Negative approval, source, requirement and evidence mutation checks."),
    "tests/test_egp_intake.py": ("013", "Manual source intake and company profile provenance."),
    "tests/test_egp_eligibility.py": ("014", "Tender-specific thresholds, units, periods, expiry and legal entity checks."),
    "tests/test_egp_workflow.py": ("015", "Integrated tender-to-company readiness workflow."),
    "tests/test_egp_regression.py": ("013-017", "Existing modules, reports, exports and historical data preserved."),
    "requirements.lock.txt": ("012", "Tested Windows dependency constraints with OCR model hashes recorded separately."),
}


def write_csv(name, rows):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    inventory = json.loads((OUT / "source_inventory_before.json").read_text())
    modules = json.loads((OUT / "architecture.json").read_text())
    with (OUT / "release011_diff.csv").open(encoding="utf-8-sig") as stream:
        diffs = {row["path"]: row["status"] for row in csv.DictReader(stream)}
    rows = []
    for item in inventory:
        name = item["path"]
        decision, release, reason, acceptance = CHANGES.get(name, ("KEEP", "011A", "Preserve existing behavior and content.", "Retain original hash in the preservation snapshot; existing applicable regressions remain green."))
        if name.startswith(("storage/", "data/")):
            decision, release, reason, acceptance = "KEEP", "011A-017", "Preserve saved documents, records, output artifacts or seed/reference assets; never use as a patch target.", "Hash and restored database counts agree with the preservation snapshot."
        imports = modules.get(name, {}).get("imports", [])
        rows.append({"path": name, "exists": True, "decision": decision, "release": release, "reason": reason, "dependencies": "; ".join(sorted({i["module"] for i in imports})), "risk": "High: decision, provenance or migration contract" if decision == "REPAIR" or name in {"tenderproof/models.py", "tenderproof/db.py"} else "Medium: additive compatibility" if decision == "EXTEND" else "Preservation", "acceptance_test": acceptance, "sha256": item["sha256"], "release011_comparison": diffs.get(name, "persistent_data_excluded_from_candidate")})
    for name, (release, purpose) in ADDITIONS.items():
        assert name not in {i["path"] for i in inventory}, name
        rows.append({"path": name, "exists": False, "decision": "ADD", "release": release, "reason": purpose, "dependencies": "Existing case/source IDs, SQLAlchemy sessions, shared decision policy and additive migration contracts as applicable", "risk": "Proposed, not implemented", "acceptance_test": "Release-specific negative, positive, data-preservation and existing-workflow regressions", "sha256": "", "release011_comparison": "proposed"})
    write_csv("IMPLEMENTATION_MANIFEST.csv", rows)

    results = json.loads((OUT / "test_results/summary.json").read_text())
    suites = {r["target"]: r for r in results if r["suite"] == "safety"}
    statuses = {k: {c["name"]: c["result"] for c in r["cases"]} for k, r in suites.items()}
    safety = [{"test": c["name"], "current": c["result"], "release011": statuses["release011"][c["name"]], "scope": "Proposed synthetic acceptance probe; passing controls do not prove complete procurement compliance"} for c in suites["current"]["cases"]]
    write_csv("SAFETY_TEST_MATRIX.csv", safety)

    findings = []
    secret_patterns = {"openai_key_shape": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}", "aws_key_shape": r"\bAKIA[0-9A-Z]{16}\b", "private_key_header": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"}
    for item in inventory:
        if item["path"].startswith(("storage/", "data/")):
            continue
        path = OUT.parent / "tenderproof_os" / item["path"]
        text = path.read_text(encoding="utf-8", errors="replace")
        for kind, pattern in secret_patterns.items():
            for match in re.finditer(pattern, text):
                findings.append({"path": item["path"], "line": text.count("\n", 0, match.start()) + 1, "kind": kind})
    (OUT / "security_inventory.json").write_text(json.dumps({"credential_pattern_hits": findings, "scope": "Application source/config/docs, excluding persistent user data and runtime dependencies", "limitations": "Pattern scan is not a secret-discovery guarantee, package vulnerability audit or penetration test.", "listener_binding_in_config": "localhost", "tenant_authorization": "No user/tenant model or authenticated application API; single local operator trust boundary."}, indent=2), encoding="utf-8")
    deps = json.loads((OUT / "installed_dependencies.json").read_text())
    (OUT / "requirements.environment_snapshot.txt").write_text("\n".join(f"{d['name']}=={d['version']}" for d in sorted(deps, key=lambda x: x['name'].casefold())) + "\n", encoding="utf-8")
    reference_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT / "references").iterdir() if p.is_file()}
    (OUT / "reference_hashes.json").write_text(json.dumps(reference_hashes, indent=2), encoding="utf-8")
    print(json.dumps({"manifest_rows": len(rows), "existing_files": len(inventory), "proposed_additions": len(ADDITIONS), "safety_probes": len(safety), "credential_pattern_hits": len(findings)}, indent=2))


if __name__ == "__main__":
    main()
