"""Fresh Release 012 checks and recovery evidence; never migrate the live database."""

import csv
import difflib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from uuid import uuid4
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
PROJECT = ROOT / "tenderproof_os"
EVIDENCE = ROOT / "evidence"
BASELINE = WORKSPACE / "release_011A_audit_2026-10-15"
PYTHON = WORKSPACE / "tenderproof_os/.venv/Scripts/python.exe"


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def save(name, data):
    (EVIDENCE / name).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def fingerprints(connection):
    values = {}
    tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    for table in tables:
        columns = [r[1] for r in connection.execute(f'PRAGMA table_info("{table}")')]
        rows = connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
        values[table] = {"columns": columns, "rows": len(rows), "sha256": hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()}
    return values


def recovery_check():
    os.environ["TENDERPROOF_RUNTIME_ROOT"] = str(ROOT / "verification_runtime")
    sys.path.insert(0, str(PROJECT))
    from tenderproof.db import init_db

    folder = EVIDENCE / f"recovery_{uuid4().hex[:8]}"
    folder.mkdir()
    original = BASELINE / "backup/storage/tenderproof.db"
    restored = folder / "migrated.db"
    shutil.copy2(original, restored)
    with sqlite3.connect(restored) as connection:
        before = fingerprints(connection)
    init_db(restored)
    first_hash = digest(restored)
    init_db(restored)
    values_preserved = {}
    with sqlite3.connect(restored) as connection:
        for table, info in before.items():
            columns = ",".join('"' + c + '"' for c in info["columns"])
            rows = connection.execute(f'SELECT {columns} FROM "{table}" ORDER BY rowid').fetchall()
            values_preserved[table] = len(rows) == info["rows"] and hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest() == info["sha256"]
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = list(connection.execute("PRAGMA foreign_key_check"))
        table_count = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    backup = next((folder / "backups").glob("*.db"))
    rollback = folder / "rollback_restored.db"
    shutil.copy2(backup, rollback)
    with sqlite3.connect(rollback) as connection:
        rollback_matches = fingerprints(connection) == before
        rollback_integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    result = {"original_tables": len(before), "migrated_tables": table_count, "old_table_values_preserved": values_preserved, "integrity_check": integrity, "foreign_key_violations": len(foreign_keys), "second_migration_byte_identical": first_hash == digest(restored), "rollback_matches_old_schema_and_values": rollback_matches, "rollback_integrity": rollback_integrity, "recovery_directory": str(folder.relative_to(ROOT))}
    result["passed"] = all(values_preserved.values()) and integrity == "ok" and not foreign_keys and result["second_migration_byte_identical"] and rollback_matches and rollback_integrity == "ok"
    save("recovery_check.json", result)
    return result["passed"]


def run_tests(label, target, env):
    xml = EVIDENCE / f"{label}.xml"
    command = [str(PYTHON), "-X", "utf8", "-B", "-m", "pytest", str(target), "-q", "--tb=short", "-p", "no:cacheprovider", f"--junitxml={xml}"]
    result = subprocess.run(command, cwd=PROJECT, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    (EVIDENCE / f"{label}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    cases = [{"name": node.attrib["name"], "file": node.attrib.get("classname"), "result": "failed" if node.find("failure") is not None else "error" if node.find("error") is not None else "skipped" if node.find("skipped") is not None else "passed"} for node in ET.parse(xml).getroot().iter("testcase")]
    return {"label": label, "exit_code": result.returncode, "command": command, "passed": sum(c["result"] == "passed" for c in cases), "failed": sum(c["result"] == "failed" for c in cases), "errors": sum(c["result"] == "error" for c in cases), "skipped": sum(c["result"] == "skipped" for c in cases), "cases": cases}


def preservation_and_manifest():
    originals = json.loads((BASELINE / "source_inventory_before.json").read_text())
    changed_originals = [r["path"] for r in originals if not (WORKSPACE / "tenderproof_os" / r["path"]).is_file() or digest(WORKSPACE / "tenderproof_os" / r["path"]) != r["sha256"]]
    archive_sha = json.loads((BASELINE / "archive_fingerprint.json").read_text())["sha256"]
    preservation = {"original_files_checked": len(originals), "changed_original_files": changed_originals, "archive_unchanged": digest(WORKSPACE / "ProposalGuard_Source_Audit.zip") == archive_sha, "merge_performed": False}
    save("preservation_check.json", preservation)
    constraints = {
        "tests/test_release_012_safety_contract.py": BASELINE / "test_safety_contract.py",
        "tests/test_release_011.py": BASELINE / "isolated/release011/tests/test_release_011.py",
    }
    same_tests = {name: digest(PROJECT / name) == digest(original) for name, original in constraints.items()}
    save("unchanged_safety_tests.json", same_tests)

    with (BASELINE / "IMPLEMENTATION_MANIFEST.csv").open(encoding="utf-8-sig") as stream:
        planned = {r["path"]: r for r in csv.DictReader(stream)}
    previous = {r["path"]: r for r in originals if not r["path"].startswith(("storage/", "data/"))}
    current = {p.relative_to(PROJECT).as_posix(): p for p in PROJECT.rglob("*") if p.is_file() and not set(p.relative_to(PROJECT).parts) & {"storage", "data", "__pycache__", ".pytest_cache", ".venv"}}
    rows, patch = [], []
    rationales = json.loads((ROOT / "change_rationales.json").read_text())
    for name in sorted(previous.keys() | current.keys()):
        old = previous.get(name)
        path = current.get(name)
        after = digest(path) if path else None
        if old and old["sha256"] == after:
            continue
        if path is None:
            raise RuntimeError(f"Existing application file disappeared: {name}")
        baseline_path = WORKSPACE / "tenderproof_os" / name
        before_text = baseline_path.read_text(encoding="utf-8-sig").splitlines(keepends=True) if old else []
        patch.extend(difflib.unified_diff(before_text, path.read_text(encoding="utf-8-sig").splitlines(keepends=True), fromfile="baseline/" + name if old else "/dev/null", tofile="release012/" + name))
        rationale = planned.get(name, {}).get("reason") or ("Enforce Release 012 safety, migration and positive workflow regression gates." if name.startswith("tests/") else "Implement shared source/evidence snapshot and approval policy.")
        if name == "tenderproof/migrations.py":
            rationale = "Transactional additive migration journal and automatic pre-migration SQLite backup."
        rationale = rationales.get(name, rationale)
        rows.append({"file": name, "change": "MODIFIED" if old else "ADDED", "before_sha256": old["sha256"] if old else "", "after_sha256": after, "rationale": rationale, "verification": "verification_audit.xml; independent_safety.xml; page_smoke.json; recovery_check.json as applicable", "rollback_reference": "../release_011A_audit_2026-10-15/backup/project_snapshot.zip; evidence/recovery_check.json"})
    with (ROOT / "CHANGE_MANIFEST.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / "release_012_review.patch").write_text("".join(patch), encoding="utf-8")
    with zipfile.ZipFile(ROOT / "release_012_changed_files.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for row in rows:
            archive.write(PROJECT / row["file"], row["file"])
    return not changed_originals and preservation["archive_unchanged"] and all(same_tests.values()), len(rows)


def main():
    env = {**os.environ, "PYTHONPATH": str(PROJECT), "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONUTF8": "1", "TENDERPROOF_RUNTIME_ROOT": str(ROOT / "verification_runtime"), "TENDERPROOF_DB_PATH": str(ROOT / "verification_runtime/storage/tenderproof.db")}
    results = []
    for label, target in (("verification_audit", "tests"), ("independent_safety", BASELINE / "test_safety_contract.py")):
        result = run_tests(label, target, env)
        results.append(result)
        print(json.dumps({k: v for k, v in result.items() if k not in {"command", "cases"}}), flush=True)
    recovery = recovery_check()
    preserved, changed = preservation_and_manifest()
    pages = json.loads((EVIDENCE / "page_smoke.json").read_text())
    summary = {"tests": results, "recovery_passed": recovery, "original_preserved_and_tests_unchanged": preserved, "application_page_smoke": {"passed": sum(not p["exceptions"] for p in pages), "total": len(pages)}, "changed_files": changed, "merge_authorization": "PENDING_USER_APPROVAL", "scope": "Isolated Release 012 candidate; no e-GP feature expansion or live release."}
    summary["engineering_gates_passed"] = all(r["exit_code"] == 0 and not r["skipped"] for r in results) and recovery and preserved and len(pages) == 16 and all(not p["exceptions"] for p in pages)
    save("verification_summary.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "tests"}, indent=2))
    return int(not summary["engineering_gates_passed"])


if __name__ == "__main__":
    raise SystemExit(main())
