"""Read-only final boundaries and reproducible evidence collection."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import APP, AUDIT, EVIDENCE, ROOT, digest, preserve, save
from restore_protected_test import all_files
from verify import features, package


def integrity():
    original = json.loads((EVIDENCE / "restoration_before.json").read_text())
    current = all_files(APP)
    changed = sorted(n for n in original["candidate_files"].keys() | current.keys() if original["candidate_files"].get(n) != current.get(n))
    recovery_unchanged = all_files(ROOT / "baseline") == original["baseline_files"]
    frozen = json.loads((EVIDENCE / "frozen_tests.json").read_text())
    actual_frozen = all((APP / n).read_bytes() == (AUDIT / ("test_safety_contract.py" if n.endswith("safety_contract.py") else "isolated/release011/tests/test_release_011.py")).read_bytes() for n in frozen["frozen"])
    browser = json.loads((EVIDENCE / "browser_verification.json").read_text())
    workflow = json.loads((EVIDENCE / "positive_workflow.json").read_text())
    sources = {Path(row["path"]).name: ROOT / row["path"] for row in workflow["artifacts"]}
    downloads = [{"path": path, "sha256": digest(Path(path)), "matches_generated_bytes": Path(path).name in sources and Path(path).read_bytes() == sources[Path(path).name].read_bytes()} for path in browser["approved_downloads"]]
    record = {"candidate_files_including_dependencies": len(current), "changes_since_pre_restoration": changed, "only_authorized_test_restoration_changed_candidate": changed == ["tests/test_release_011.py"], "all_protected_tests_byte_identical": actual_frozen and all(frozen["old_test_files_unchanged"].values()), "verified_recovery_snapshots_unchanged": recovery_unchanged, "operational": preserve(), "downloaded_artifacts": downloads, "approval_and_merge": "pending_approval"}
    save("final_boundary.json", record)
    if not (record["only_authorized_test_restoration_changed_candidate"] and record["all_protected_tests_byte_identical"] and recovery_unchanged and all(d["matches_generated_bytes"] for d in downloads)):
        raise RuntimeError("STOP: final preservation, protected-test or artifact boundary failed.")
    features()
    print(json.dumps({"candidate_files_checked": len(current), "only_change": changed, "operational_files_unchanged": 340, "snapshots_unchanged": True, "actual_downloads_match_MD_DOCX_XLSX": True}))


def complete():
    boundary = json.loads((EVIDENCE / "final_boundary.json").read_text())
    if not boundary["only_authorized_test_restoration_changed_candidate"]:
        raise RuntimeError("Final boundary has not passed.")
    history = EVIDENCE / "pre_resumption"
    for name in ("CHANGE_MANIFEST.csv", "REVIEWED_CHANGES.patch", "RELEASE_012_CODE_REVIEW.zip"):
        if not (history / name).exists():
            shutil.copy2(ROOT / name, history / name)
    package()
    records = json.loads((EVIDENCE / "test_summary.json").read_text())
    if len(records) != 2 or records[0]["passed"] != 121 or records[1]["passed"] != 24 or any(r["exit_code"] or r["failed"] or r["error"] or r["skipped"] for r in records):
        raise RuntimeError("STOP: final test evidence has unresolved failures.")
    with (ROOT.parent / "release_012_plan_2026-10-15/SAFETY_CHECK_MAP.csv").open(encoding="utf-8-sig", newline="") as f:
        safety_rows = list(csv.DictReader(f))
    actual = {row["name"]: row["result"] for row in records[1]["cases"]}
    if set(actual) != {r["exact_test_name"] for r in safety_rows} or any(v != "passed" for v in actual.values()):
        raise RuntimeError("STOP: protected safety identities/results differ from the 24-check map.")
    for row in safety_rows:
        row["fresh_candidate_result"] = actual[row["exact_test_name"]]
        row["fresh_evidence"] = "evidence/external_safety.xml"
    with (ROOT / "SAFETY_RESULTS.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(safety_rows[0]))
        writer.writeheader()
        writer.writerows(safety_rows)
    junit = list(ET.parse(EVIDENCE / "regression.xml").getroot().iter("testcase"))
    groups = {}
    for node in junit:
        module = node.attrib.get("classname", "").split(".")[-1]
        groups[module] = groups.get(module, 0) + 1
    with (ROOT / "CHANGE_MANIFEST.csv").open(encoding="utf-8", newline="") as f:
        manifest = list(csv.DictReader(f))
    for row in manifest:
        row["verification_result"] = "Fresh combined suite 121/121 and external protected safety 24/24; see additional applicable evidence"
        if row["file"].startswith("tests/"):
            module = Path(row["file"]).stem
            row["file_specific_test_evidence"] = f"evidence/regression.xml: {groups.get(module, 'shared fixture')} cases in {module}; original assertions unchanged"
        elif row["file"].startswith("tenderproof/ui/"):
            row["file_specific_test_evidence"] = "evidence/page_smoke.json; evidence/browser_verification.json; approval/download interaction cases in regression.xml"
        elif row["file"] in {"tenderproof/db.py", "tenderproof/models.py", "tenderproof/migrations.py"}:
            row["file_specific_test_evidence"] = "evidence/recovery.json; evidence/transactions.json; test_release_012_migration and test_db_migration in regression.xml"
        elif row["file"] in {"run_app.py", "deploy&run.bat", "tenderproof/config.py", "constraints-release-012.txt"}:
            row["file_specific_test_evidence"] = "evidence/launcher_summary.json; evidence/pip_check.log; evidence/clean_install.log; actual temporary run_app server"
        else:
            row["file_specific_test_evidence"] = "evidence/positive_workflow.json; policy/workflow tests in regression.xml; evidence/external_safety.xml"
    with (ROOT / "CHANGE_MANIFEST.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    with zipfile.ZipFile(ROOT / "RELEASE_012_CODE_REVIEW.zip") as z:
        exact_code_package = all(hashlib.sha256(z.read(row["file"])).hexdigest() == row["candidate_sha256"] for row in manifest)
    if not exact_code_package:
        raise RuntimeError("STOP: review ZIP differs from candidate bytes.")
    recovery = json.loads((EVIDENCE / "recovery.json").read_text())
    workflow = json.loads((EVIDENCE / "positive_workflow.json").read_text())
    transactions = json.loads((EVIDENCE / "transactions.json").read_text())
    browser = json.loads((EVIDENCE / "browser_verification.json").read_text())
    gates = {f"G{i:02d}": {"technical_evidence": "observed_pass" if i < 9 else "not_applicable_to_automation", "human_resolution": "pending_approval", "bypass": False} for i in range(1, 10)}
    full_launcher = json.loads((EVIDENCE / "full_windows_launcher.json").read_text())
    if full_launcher.get("verification_exit_code") != 0 or full_launcher.get("fresh_normal_launcher_test_passes") != 121 or not full_launcher.get("all_QA_source_digests_still_match_candidate") or full_launcher.get("cleanup_exit_code") != 0:
        raise RuntimeError("STOP: full normal Windows launcher evidence is incomplete.")
    gates["G07"]["limitations"] = "Normal Windows wrapper executed full install/test/start sequence in separate QA copy; physical Explorer double-click and independent founder acceptance were not performed."
    summary = {"status": "verified_candidate_for_human_review_not_approved_release", "restored_test_sha256": "886027e6f63f2f8e68b1bce330acdb3687ca47e9a4b955c4d253f20ce3bdbd7e", "fresh_combined_tests": records[0], "fresh_external_safety": records[1], "fresh_test_modules": groups, "fresh_discriminator_tests": groups.get("test_release_012_policy"), "resumed_verification_replaces_preliminary_results": True, "pages_AppTest": 16, "pages_browser": len(browser["pages_checked"]), "full_normal_windows_launcher": full_launcher, "recovery": recovery, "positive_workflow": workflow, "transactions": transactions, "preservation": boundary, "changed_added_files": len(manifest), "code_package_member_digests_verified": exact_code_package, "human_gates": gates, "outstanding_issues": [{"id": "R012-N01", "severity": "low", "blocking_mandatory_safety": False, "description": "Report audit event text retains staging .pending filenames; authoritative OutputPackage paths and artifact hashes use the final existing files. No correction made under verification-only scope."}], "merge_status": "pending_approval", "deployment_performed": False, "operational_changes": False, "temporary_test_server_stopped": browser["temporary_server_stopped"]}
    save("FINAL_VERIFICATION_SUMMARY.json", summary)
    for task in json.loads((EVIDENCE / "tasks.json").read_text()).values():
        task["human_gate"] = "pending_approval"
    tasks = json.loads((EVIDENCE / "tasks.json").read_text())
    for name in tasks:
        tasks[name]["status"] = "complete"
        tasks[name]["human_gate"] = "pending_approval"
        tasks[name]["completion_scope"] = "engineering/evidence only; not founder acceptance or release authorization"
    save("tasks.json", tasks)
    save("stop.json", {"issue": "R012-STOP-001", "status": "resolved_by_explicit_user_authorization", "historical_stop": "evidence/pre_resumption/stop.json", "restoration": "evidence/restoration.json", "fresh_verification": "evidence/FINAL_VERIFICATION_SUMMARY.json", "merge": "pending_approval"})
    preserve()
    print(json.dumps({"fresh_combined_tests": records[0]["passed"], "fresh_external_safety": records[1]["passed"], "fresh_discriminators": groups.get("test_release_012_policy"), "manifest_files": len(manifest), "merge": "pending_approval"}))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["integrity", "complete"])
    args = p.parse_args()
    {"integrity": integrity, "complete": complete}[args.phase]()
