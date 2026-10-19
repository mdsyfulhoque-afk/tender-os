"""Preservation-first workspace preparation and reviewed patch generation."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import zipfile

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
OPERATIONAL = WORKSPACE / "tenderproof_os"
AUDIT = WORKSPACE / "release_011A_audit_2026-10-15"
EXPERIMENT = WORKSPACE / "release_012_safety" / "tenderproof_os"
APP = ROOT / "tenderproof_os"
EVIDENCE = ROOT / "evidence"
EXCLUDED = {".venv", ".git", "__pycache__", ".pytest_cache", "tmp"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(name, value):
    EVIDENCE.mkdir(exist_ok=True)
    (EVIDENCE / name).write_text(json.dumps(value, indent=2, default=str), encoding="utf-8")


def inventory():
    return json.loads((AUDIT / "source_inventory_before.json").read_text(encoding="utf-8-sig"))


def preserve():
    bad = [r["path"] for r in inventory() if not (OPERATIONAL / r["path"]).is_file() or digest(OPERATIONAL / r["path"]) != r["sha256"]]
    observed = set()
    for base, folders, files in os.walk(OPERATIONAL):
        folders[:] = [name for name in folders if name not in EXCLUDED]
        observed.update((Path(base) / name).relative_to(OPERATIONAL).as_posix() for name in files)
    unexpected = sorted(observed - {r["path"] for r in inventory()})
    archive_ok = digest(WORKSPACE / "ProposalGuard_Source_Audit.zip") == "8a3f4b2a5c8aa8e86bd47c47906dba4c3621cbb508383290132f41a9eba6ca55"
    result = {"checked": len(inventory()), "unchanged": not bad and not unexpected and archive_ok, "discrepancies": bad, "unexpected_files": unexpected, "source_archive_unchanged": archive_ok}
    save("preservation_latest.json", result)
    if not result["unchanged"]:
        raise RuntimeError(f"STOP: operational preservation discrepancy: {result}")
    return result


def db_fingerprint(path):
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        names = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        values = {}
        for name in names:
            columns = list(db.execute(f'PRAGMA table_info("{name}")'))
            rows = db.execute(f'SELECT * FROM "{name}" ORDER BY id').fetchall()
            values[name] = {"columns": columns, "rows": rows}
        return {"integrity": db.execute("PRAGMA integrity_check").fetchone()[0], "tables": values}


def prepare():
    preserve()
    if APP.exists():
        raise RuntimeError("Workspace already prepared; refusing to overwrite it.")
    baseline = ROOT / "baseline"
    baseline.mkdir(exist_ok=False)
    for item in inventory():
        target = APP / item["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(OPERATIONAL / item["path"], target)
    db_path = baseline / "tenderproof.db"
    with sqlite3.connect((OPERATIONAL / "storage/tenderproof.db").as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(db_path) as target:
        source.backup(target)
    if db_fingerprint(db_path) != db_fingerprint(OPERATIONAL / "storage/tenderproof.db"):
        raise RuntimeError("STOP: consistent baseline backup differs in schema or record values.")
    with zipfile.ZipFile(baseline / "project_snapshot.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for item in inventory():
            z.write(db_path if item["path"] == "storage/tenderproof.db" else OPERATIONAL / item["path"], item["path"])
    with zipfile.ZipFile(baseline / "project_snapshot.zip") as z:
        member_hashes = {name: hashlib.sha256(z.read(name)).hexdigest() for name in z.namelist()}
    save("baseline.json", {"inventory": inventory(), "snapshot_sha256": digest(baseline / "project_snapshot.zip"), "snapshot_member_sha256": member_hashes, "database_values": db_fingerprint(db_path), "plan_sha256": digest(WORKSPACE / "release_012_plan_2026-10-15/RELEASE_012_SAFETY_INTEGRATION_PLAN.md"), "implementation": "approved_isolated_only", "merge": "pending_approval"})
    save("tasks.json", {f"T{i:02d}": {"status": "complete" if i == 0 else "pending", "locked": False, "human_gate": "pending"} for i in range(10)})
    preserve()
    print("T00 complete: 340-file operational baseline preserved; separate working copy and consistent recovery snapshot created.")


def patch(paths):
    preserve()
    with (WORKSPACE / "release_012_safety/CHANGE_MANIFEST.csv").open(encoding="utf-8-sig", newline="") as f:
        reviewed = {r["file"]: r for r in csv.DictReader(f)}
    output = ["*** Begin Patch"]
    records = []
    for name in paths:
        if name not in reviewed or not (EXPERIMENT / name).is_file():
            raise RuntimeError(f"Unreviewed patch source: {name}")
        entry = reviewed[name]
        if digest(EXPERIMENT / name) != entry["after_sha256"]:
            raise RuntimeError(f"STOP: experimental source changed unexpectedly: {name}")
        target = APP / name
        if target.exists():
            if digest(target) != entry["before_sha256"]:
                raise RuntimeError(f"STOP: target no longer equals operational baseline: {name}")
            output.extend([f"*** Update File: {target.as_posix()}", "@@"])
            output.extend("-" + line for line in target.read_text(encoding="utf-8-sig").splitlines())
        else:
            output.append(f"*** Add File: {target.as_posix()}")
        output.extend("+" + line for line in (EXPERIMENT / name).read_text(encoding="utf-8-sig").splitlines())
        records.append({"file": name, "source_sha256": digest(EXPERIMENT / name), "baseline_sha256": entry["before_sha256"], "rationale": entry["rationale"], "review": "selected individual file; further controlled repairs and fresh verification required"})
    output.append("*** End Patch")
    ledger_path = EVIDENCE / "selective_port_ledger.json"
    prior = json.loads(ledger_path.read_text()) if ledger_path.exists() else []
    save("selective_port_ledger.json", prior + records)
    print("\n".join(output))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare", "preserve", "patch", "status"])
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "preserve":
        print(json.dumps(preserve()))
    elif args.command == "status":
        state = json.loads((EVIDENCE / "tasks.json").read_text())
        for item in args.paths:
            task, value = item.split(":")
            if task not in state or value not in {"pending", "in_progress", "complete", "blocked"}:
                raise ValueError("Invalid engineering task update")
            state[task]["status"] = value
        save("tasks.json", state)
        print(json.dumps(state))
    else:
        patch(args.paths)
