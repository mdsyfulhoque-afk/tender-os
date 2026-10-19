"""Fresh isolated verification and evidence packaging; never deploys or approves."""

import argparse
import ast
import csv
import difflib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import APP, AUDIT, EVIDENCE, OPERATIONAL, ROOT, WORKSPACE, digest, inventory, preserve, save

PYTHON = APP / ".venv/Scripts/python.exe"


def environment(label):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(APP), TENDERPROOF_RUNTIME_ROOT=str(ROOT / "runtime" / label))
    env.pop("TENDERPROOF_DB_PATH", None)
    return env


def command(label, args, *, cwd=APP, env=None, timeout=600):
    preserve()
    result = subprocess.run(args, cwd=cwd, env=env or environment(label), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    (EVIDENCE / f"{label}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    record = {"label": label, "command": list(map(str, args)), "cwd": str(cwd), "exit_code": result.returncode, "log": f"evidence/{label}.log"}
    save(f"{label}_command.json", record)
    preserve()
    return record


def tests():
    references = {"tests/test_release_012_safety_contract.py": AUDIT / "test_safety_contract.py", "tests/test_release_011.py": AUDIT / "isolated/release011/tests/test_release_011.py"}
    hashes = {name: {"reference_sha256": digest(path), "candidate_sha256": digest(APP / name), "identical": path.read_bytes() == (APP / name).read_bytes()} for name, path in references.items()}
    originals = {r["path"]: r for r in inventory() if r["path"].startswith("tests/") and r["path"] != "tests/conftest.py"}
    save("frozen_tests.json", {"frozen": hashes, "old_test_files_unchanged": {name: digest(APP / name) == r["sha256"] for name, r in originals.items()}})
    if not all(v["identical"] for v in hashes.values()) or not all(digest(APP / n) == r["sha256"] for n, r in originals.items()):
        raise RuntimeError("STOP: protected tests changed.")
    records = []
    for label, target in (("regression", "tests"), ("external_safety", str(AUDIT / "test_safety_contract.py"))):
        xml = EVIDENCE / f"{label}.xml"
        record = command(label, [str(PYTHON), "-B", "-m", "pytest", target, "-q", "--tb=short", "-p", "no:cacheprovider", f"--junitxml={xml}"])
        cases = [{"name": n.attrib["name"], "result": "failed" if n.find("failure") is not None else "error" if n.find("error") is not None else "skipped" if n.find("skipped") is not None else "passed"} for n in ET.parse(xml).getroot().iter("testcase")]
        record.update({"cases": cases, **{state: sum(c["result"] == state for c in cases) for state in ("passed", "failed", "error", "skipped")}})
        records.append(record)
        save("test_summary.json", records)
        print(f"{label}: {record['passed']} passed; {record['failed']} failed; {record['error']} errors; {record['skipped']} skipped", flush=True)
        if record["exit_code"] or any(record[k] for k in ("failed", "error", "skipped")):
            raise RuntimeError(f"STOP: unresolved verification failure; inspect {record['log']}")
    if len(records[1]["cases"]) != 24:
        raise RuntimeError("STOP: external safety collection was not exactly 24.")


def recovery():
    os.environ.update(environment("recovery"))
    sys.path.insert(0, str(APP))
    from tenderproof.db import init_db

    folder = EVIDENCE / "recovery"
    folder.mkdir(exist_ok=False)
    target = folder / "migrated.db"
    shutil.copy2(ROOT / "baseline/tenderproof.db", target)
    with sqlite3.connect(target) as db:
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        before = {t: {"columns": [r[1] for r in db.execute(f'PRAGMA table_info("{t}")')], "rows": db.execute(f'SELECT * FROM "{t}" ORDER BY id').fetchall()} for t in tables}
    init_db(target)
    first = digest(target)
    init_db(target)
    preserved = {}
    with sqlite3.connect(target) as db:
        for table, info in before.items():
            columns = ",".join('"' + c + '"' for c in info["columns"])
            preserved[table] = db.execute(f'SELECT {columns} FROM "{table}" ORDER BY id').fetchall() == info["rows"]
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        fks = db.execute("PRAGMA foreign_key_check").fetchall()
        journal = db.execute("SELECT version,checksum,recovery_reference FROM schema_migrations").fetchall()
        new_tables = db.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    backup = next((folder / "backups").glob("*.db"))
    restore = folder / "restored.db"
    shutil.copy2(backup, restore)
    with sqlite3.connect(restore) as db:
        same_tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")] == tables
        restored_values = all(db.execute(f'SELECT * FROM "{t}" ORDER BY id').fetchall() == value["rows"] for t, value in before.items())
        restored_schema = all([r[1] for r in db.execute(f'PRAGMA table_info("{t}")')] == value["columns"] for t, value in before.items())
        restored_integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    result = {"original_tables": len(tables), "migrated_tables": new_tables, "all_old_values_preserved": preserved, "integrity": integrity, "foreign_key_violations": fks, "second_initialization_byte_identical": first == digest(target), "migration_journal": journal, "restore_tables_match": same_tables, "restore_schema_match": restored_schema, "restore_values_match": restored_values, "restore_integrity": restored_integrity, "recovery_path": str(folder.relative_to(ROOT))}
    result["technical_observation_passed"] = all(preserved.values()) and integrity == "ok" and not fks and result["second_initialization_byte_identical"] and same_tables and restored_values and restored_schema and restored_integrity == "ok"
    save("recovery.json", result)
    preserve()
    if not result["technical_observation_passed"]:
        raise RuntimeError("STOP: recovery verification failed.")
    print("Recovery: 17 old tables retained; 21 after additive migration; all old values and restored schema/values match.", flush=True)


def features():
    def pages(path):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        return next([k.value for k in n.value.keys] for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PAGES" for t in n.targets))

    old_pages, new_pages = pages(OPERATIONAL / "app.py"), pages(APP / "app.py")
    def sheets(path):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        return next([item.elts[0].value for item in n.value.elts] for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SHEET_MODELS" for t in n.targets))

    old_sheets = sheets(OPERATIONAL / "tenderproof/services/export_service.py")
    new_sheets = sheets(APP / "tenderproof/services/export_service.py")
    def headings(path):
        return [n.value for n in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))) if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.startswith("## ")]

    old_sections = headings(OPERATIONAL / "tenderproof/services/report_service.py")
    new_sections = headings(APP / "tenderproof/services/report_service.py")
    assets = {r["path"]: digest(APP / r["path"]) == r["sha256"] for r in inventory() if r["path"].startswith(("data/", "storage/", "tenderproof/prompts/", "tenderproof/templates/"))}
    result = {"pages": new_pages, "pages_preserved": old_pages == new_pages and len(new_pages) == 16, "workbook_sheets": new_sheets, "sheets_preserved": old_sheets == new_sheets and len(new_sheets) == 16, "old_report_sections": old_sections, "report_sections_preserved": all(s in new_sections for s in old_sections), "launchers_present": all((APP / n).is_file() for n in ("deploy&run.bat", "deploy_and_run.bat")), "preserved_data_and_assets": len(assets), "asset_discrepancies": [n for n, good in assets.items() if not good]}
    save("preserved_features.json", result)
    if not (result["pages_preserved"] and result["sheets_preserved"] and result["report_sections_preserved"] and result["launchers_present"] and not result["asset_discrepancies"]):
        raise RuntimeError("STOP: existing feature or asset preservation mismatch.")


def package():
    preserve()
    features()
    reference = {r["path"]: r for r in inventory() if not r["path"].startswith(("data/", "storage/"))}
    current = {}
    for base, folders, files in os.walk(APP):
        folders[:] = [f for f in folders if f not in {".venv", "__pycache__", ".pytest_cache", "data", "storage"}]
        for name in files:
            p = Path(base) / name
            current[p.relative_to(APP).as_posix()] = p
    ledger = {r["file"]: r for r in json.loads((EVIDENCE / "selective_port_ledger.json").read_text())}
    rationales = json.loads((ROOT / "change_rationales.json").read_text())
    rows, patch = [], []
    for name in sorted(reference.keys() | current.keys()):
        old, new = reference.get(name), current.get(name)
        if new is None:
            raise RuntimeError(f"STOP: original application file removed: {name}")
        if old and old["sha256"] == digest(new):
            continue
        rationale = rationales.get(name) or ledger.get(name, {}).get("rationale")
        if not rationale:
            raise RuntimeError(f"STOP: changed file lacks reviewed rationale: {name}")
        rows.append({"file": name, "change": "MODIFIED" if old else "ADDED", "baseline_sha256": old["sha256"] if old else "", "candidate_sha256": digest(new), "experimental_source_sha256": ledger.get(name, {}).get("source_sha256", ""), "rationale": rationale, "test_evidence": "evidence/test_summary.json; evidence/recovery.json; evidence/preserved_features.json; evidence/page_smoke.json as applicable", "recovery_reference": "baseline/project_snapshot.zip; baseline/tenderproof.db; evidence/baseline.json", "human_review": "pending_approval"})
        before = (OPERATIONAL / name).read_text(encoding="utf-8-sig").splitlines(keepends=True) if old else []
        patch.extend(difflib.unified_diff(before, new.read_text(encoding="utf-8-sig").splitlines(keepends=True), fromfile="a/" + name, tofile="b/" + name))
    with (ROOT / "CHANGE_MANIFEST.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (ROOT / "REVIEWED_CHANGES.patch").write_text("".join(patch), encoding="utf-8")
    with zipfile.ZipFile(ROOT / "RELEASE_012_CODE_REVIEW.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for row in rows:
            z.write(APP / row["file"], row["file"])
    save("package.json", {"changed_or_added_files": len(rows), "code_package_sha256": digest(ROOT / "RELEASE_012_CODE_REVIEW.zip"), "patch_sha256": digest(ROOT / "REVIEWED_CHANGES.patch"), "contains_client_storage_or_database": False, "merge": "pending_approval", "deployment": "not_authorized"})
    print(f"Review package: {len(rows)} changed/added files; no client storage; merge pending approval.", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["tests", "recovery", "features", "package"])
    args = p.parse_args()
    {"tests": tests, "recovery": recovery, "features": features, "package": package}[args.phase]()
