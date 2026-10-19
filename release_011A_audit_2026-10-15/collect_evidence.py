"""Collect Release 011A evidence without importing or changing the live application."""

import ast
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
import zipfile


OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
PROJECT = ROOT / "tenderproof_os"
CANDIDATE = Path(os.environ.get("PG_RELEASE_011_CANDIDATE", str(Path(os.environ["TEMP"]) / "PG_Release_011_101692bea9404c14b69c3d9395c4506b")))
ARCHIVE = ROOT / "ProposalGuard_Source_Audit.zip"
EXCLUDE = {".venv", ".git", "__pycache__", ".pytest_cache", "tmp"}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(name, data):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def paths(root, persistent=True):
    excluded = EXCLUDE | (set() if persistent else {"data", "storage"})
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in excluded and not (Path(base) / d).is_symlink())
        for name in sorted(files):
            path = Path(base) / name
            if not path.is_symlink():
                yield path


def inventory(root):
    return [{"path": p.relative_to(root).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p)} for p in paths(root)]


def write_csv(name, rows, fields):
    with (OUT / name).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def inspect_python(root):
    modules = {}
    for path in paths(root, persistent=False):
        if path.suffix != ".py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        imports, definitions = [], []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.append({"line": node.lineno, "module": "." * node.level + (node.module or ""), "names": [a.name for a in node.names]})
            elif isinstance(node, ast.Import):
                imports.append({"line": node.lineno, "module": ",".join(a.name for a in node.names)})
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions.append({"name": node.name, "line": node.lineno, "signature": ast.unparse(node.args)})
            elif isinstance(node, ast.ClassDef):
                definitions.append({"name": node.name, "line": node.lineno, "class": True})
        modules[path.relative_to(root).as_posix()] = {"imports": imports, "definitions": definitions}
    return modules


def database_snapshot():
    source = PROJECT / "storage" / "tenderproof.db"
    target = OUT / "backup" / "storage" / "tenderproof.db"
    target.parent.mkdir(parents=True, exist_ok=True)
    source_hash = sha(source)
    schema = {"source_sha256": source_hash, "access": "SQLite URI mode=ro, query_only=ON", "tables": {}}
    with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        schema["integrity_check"] = connection.execute("PRAGMA integrity_check").fetchone()[0]
        schema["journal_mode"] = connection.execute("PRAGMA journal_mode").fetchone()[0]
        schema["user_version"] = connection.execute("PRAGMA user_version").fetchone()[0]
        tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for name in tables:
            quoted = '"' + name.replace('"', '""') + '"'
            columns = [dict(r) for r in connection.execute(f"PRAGMA table_info({quoted})")]
            info = {
                "rows": connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0],
                "columns": columns,
                "foreign_keys": [dict(r) for r in connection.execute(f"PRAGMA foreign_key_list({quoted})")],
                "indexes": [dict(r) for r in connection.execute(f"PRAGMA index_list({quoted})")],
                "sql": connection.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()[0],
            }
            if name != "cases" and any(c["name"] == "case_id" for c in columns):
                info["orphan_case_links"] = connection.execute(f"SELECT COUNT(*) FROM {quoted} x LEFT JOIN cases c ON c.case_id=x.case_id WHERE x.case_id IS NOT NULL AND c.case_id IS NULL").fetchone()[0]
            schema["tables"][name] = info
        schema["compliance_requirement_mismatch"] = connection.execute("SELECT COUNT(*) FROM compliance_ledger c LEFT JOIN normalized_requirements r ON r.requirement_id=c.requirement_id AND r.case_id=c.case_id WHERE r.id IS NULL").fetchone()[0]
        schema["missing_source_artifacts"] = {}
        for field in ("file_path", "text_extract_path"):
            schema["missing_source_artifacts"][field] = sum(1 for row in connection.execute(f"SELECT {field} FROM sources") if row[0] and not Path(row[0]).is_file())
        schema["missing_output_artifacts"] = sum(1 for row in connection.execute("SELECT file_path FROM output_packages") if row[0] and not Path(row[0]).is_file())
        with sqlite3.connect(target) as backup:
            connection.backup(backup)
    with sqlite3.connect(target.as_uri() + "?mode=ro", uri=True) as connection:
        restored_counts = {name: connection.execute('SELECT COUNT(*) FROM "' + name + '"').fetchone()[0] for name in tables}
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    schema["backup_verified"] = integrity == "ok" and all(restored_counts[n] == schema["tables"][n]["rows"] for n in tables)
    schema["source_hash_unchanged"] = sha(source) == source_hash
    write_json("database_schema.json", schema)
    return target, schema


def prepare():
    if (OUT / "source_inventory_before.json").exists():
        raise SystemExit("Evidence already exists; use --verify to check preservation.")
    before = inventory(PROJECT)
    write_json("source_inventory_before.json", before)
    write_csv("file_inventory.csv", before, ["path", "bytes", "sha256"])
    write_json("archive_fingerprint.json", {"path": ARCHIVE.name, "bytes": ARCHIVE.stat().st_size, "sha256": sha(ARCHIVE)})
    modules = inspect_python(PROJECT)
    candidate_modules = inspect_python(CANDIDATE)
    write_json("architecture.json", modules)

    diff_rows, patches, api = [], [], []
    current = {p.relative_to(PROJECT).as_posix(): p for p in paths(PROJECT, persistent=False)}
    candidate = {p.relative_to(CANDIDATE).as_posix(): p for p in paths(CANDIDATE, persistent=False)}
    for name in sorted(current.keys() | candidate.keys()):
        old, new = current.get(name), candidate.get(name)
        state = "current_only" if new is None else "candidate_only" if old is None else "identical" if sha(old) == sha(new) else "changed"
        if state == "changed":
            old_text = old.read_text(encoding="utf-8-sig").splitlines(keepends=True)
            new_text = new.read_text(encoding="utf-8-sig").splitlines(keepends=True)
            state = "line_endings_only" if old_text == new_text else "changed"
            if state == "changed":
                patches.extend(difflib.unified_diff(old_text, new_text, fromfile="current/" + name, tofile="release011/" + name))
                old_api = {d["name"]: d.get("signature", "class") for d in modules.get(name, {}).get("definitions", []) if not d["name"].startswith("_")}
                new_api = {d["name"]: d.get("signature", "class") for d in candidate_modules.get(name, {}).get("definitions", []) if not d["name"].startswith("_")}
                api.append({"path": name, "public_signatures_equal": old_api == new_api, "current": old_api, "candidate": new_api})
        diff_rows.append({"path": name, "status": state, "current_sha256": sha(old) if old else "", "candidate_sha256": sha(new) if new else ""})
    write_csv("release011_diff.csv", diff_rows, ["path", "status", "current_sha256", "candidate_sha256"])
    (OUT / "release011_changes.patch").write_text("".join(patches), encoding="utf-8")
    write_json("api_compatibility.json", api)

    archive_compare = []
    with zipfile.ZipFile(ARCHIVE) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = info.filename
            path = PROJECT / name
            digest = hashlib.sha256(archive.read(info)).hexdigest()
            archive_compare.append({"path": name, "archive_sha256": digest, "status": "identical" if path.is_file() and sha(path) == digest else "changed" if path.is_file() else "archive_only"})
    write_csv("archive_to_current.csv", archive_compare, ["path", "archive_sha256", "status"])

    backup_db, schema = database_snapshot()
    snapshot = OUT / "backup" / "project_snapshot.zip"
    expected_hashes = {}
    with zipfile.ZipFile(snapshot, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for row in before:
            name = row["path"]
            if name.endswith(("tenderproof.db-wal", "tenderproof.db-shm", "tenderproof.db-journal")):
                continue
            source = backup_db if name == "storage/tenderproof.db" else PROJECT / name
            archive.write(source, name)
            expected_hashes[name] = sha(source)
    with zipfile.ZipFile(snapshot) as archive:
        restored_ok = archive.testzip() is None and all(hashlib.sha256(archive.read(n)).hexdigest() == h for n, h in expected_hashes.items())
        extracted_db = OUT / "backup" / "restore_check.db"
        extracted_db.write_bytes(archive.read("storage/tenderproof.db"))
    with sqlite3.connect(extracted_db.as_uri() + "?mode=ro", uri=True) as connection:
        restore_ok = connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok" and all(connection.execute('SELECT COUNT(*) FROM "' + n + '"').fetchone()[0] == info["rows"] for n, info in schema["tables"].items())
    write_json("backup_manifest.json", {"snapshot": str(snapshot.relative_to(OUT)), "sha256": sha(snapshot), "member_sha256": expected_hashes, "all_members_read_back_and_hashed": restored_ok, "sqlite_restored_integrity_and_counts_match": restore_ok, "excluded_directories": sorted(EXCLUDE), "note": "Runtime is reproducible from dependency evidence; private case files are retained in this local backup."})

    for label, source in (("current", PROJECT), ("release011", CANDIDATE)):
        target = OUT / "isolated" / label
        for path in paths(source, persistent=False):
            relative = path.relative_to(source)
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)

    python = PROJECT / ".venv" / "Scripts" / "python.exe"
    for args, name in ((["-m", "pip", "list", "--format=json"], "installed_dependencies.json"), (["-m", "pip", "check"], "dependency_check.txt"), (["-VV"], "python_version.txt")):
        result = subprocess.run([str(python), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
        (OUT / name).write_text(result.stdout + result.stderr, encoding="utf-8")
    print(json.dumps({"project_files": len(before), "python_modules": len(modules), "db_tables": len(schema["tables"]), "backup_verified": restored_ok and restore_ok, "changed_candidate_files": [r["path"] for r in diff_rows if r["status"] == "changed"], "archive_differences": [r for r in archive_compare if r["status"] != "identical"]}, indent=2))


def verify():
    before = json.loads((OUT / "source_inventory_before.json").read_text(encoding="utf-8"))
    after = inventory(PROJECT)
    old, new = {r["path"]: r for r in before}, {r["path"]: r for r in after}
    changes = [n for n in sorted(old.keys() | new.keys()) if old.get(n) != new.get(n)]
    archive_hash = json.loads((OUT / "archive_fingerprint.json").read_text())["sha256"]
    result = {"unchanged": not changes and sha(ARCHIVE) == archive_hash, "project_files_checked": len(before), "changed_paths": changes, "archive_hash_unchanged": sha(ARCHIVE) == archive_hash, "runtime_and_cache_exclusions": sorted(EXCLUDE)}
    write_json("preservation_check.json", result)
    print(json.dumps(result, indent=2))
    if not result["unchanged"]:
        raise SystemExit(1)


if __name__ == "__main__":
    verify() if "--verify" in sys.argv else prepare()
