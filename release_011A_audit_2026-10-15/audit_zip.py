#!/usr/bin/env python3
"""Read-only ZIP inventory. Does not execute archive contents."""
import hashlib
import json
import platform
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

MAX_ENTRIES = 30000
MAX_TOTAL = 512 * 1024 * 1024
MAX_SINGLE = 128 * 1024 * 1024
MAX_SCAN = 2 * 1024 * 1024

SKIP_PARTS = {
    "node_modules", ".git", "dist", "build",
    "coverage", ".next", "__pycache__"
}
SOURCE_EXT = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".py", ".json", ".md", ".yml", ".yaml",
    ".toml", ".sql", ".html", ".css"
}
PATTERNS = {
    "mandatory_rules":
        r"mandatory|eligib|disqualif|hard.?block|no.?bid",
    "decision_logic":
        r"decision|approval|override|hold|bid.?status",
    "evidence":
        r"evidence|provenance|citation|validat|expir",
    "amendments":
        r"amendment|revision|version|invalidate|stale",
    "authorization":
        r"authoriz|permission|tenant|organi[sz]ation|rbac",
    "data_storage":
        r"database|persist|storage|sqlite|db\.json",
    "integrations":
        r"openai|anthropic|bedrock|azure|e.?gp",
    "reporting":
        r"export|report|pdf|csv|download"
}

def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def safe_name(name):
    if not name or "\\" in name or name.startswith("/"):
        return False
    if re.match(r"^[A-Za-z]:", name):
        return False
    parts = PurePosixPath(name).parts
    return ".." not in parts

def source_candidate(name):
    p = PurePosixPath(name)
    if SKIP_PARTS.intersection(p.parts):
        return False
    if any(x in p.parts for x in ("data", "secrets")):
        return False
    if p.name.startswith(".env"):
        return False
    return p.suffix.lower() in SOURCE_EXT

def main():
    if len(sys.argv) != 3:
        sys.exit(
            "Usage: python3 -I -B audit_zip.py "
            "'Proposal Guard.zip' audit_manifest.json"
        )

    archive = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()

    if not archive.is_file() or not zipfile.is_zipfile(archive):
        sys.exit("ERROR: Input is not a readable ZIP file.")
    if archive == output:
        sys.exit("ERROR: Output must differ from the original ZIP.")

    before_hash = sha256_file(archive)
    report = {
        "archive": archive.name,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": before_hash,
        "python_version": platform.python_version(),
        "files": [],
        "candidate_tests": [],
        "package_manifests": [],
        "source_indicators": {key: [] for key in PATTERNS},
        "limitations": [
            "Static inspection only",
            "Keyword matches do not prove implemented behavior",
            "No application code or tests executed",
            "Large source files are hashed but not text-scanned",
            "Nested archives are not inspected"
        ]
    }

    with zipfile.ZipFile(archive, "r") as z:
        infos = z.infolist()

        if len(infos) > MAX_ENTRIES:
            sys.exit("STOP: Archive exceeds member safety limit.")

        total = sum(i.file_size for i in infos)
        if total > MAX_TOTAL:
            sys.exit("STOP: Archive exceeds uncompressed size limit.")

        names = set()
        for info in infos:
            name = info.filename

            if name in names:
                sys.exit(f"STOP: Duplicate member path: {name}")
            names.add(name)

            if not safe_name(name):
                sys.exit(f"STOP: Unsafe member path: {name}")

            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                sys.exit(f"STOP: Symlink member: {name}")

            if info.flag_bits & 1:
                sys.exit(f"STOP: Encrypted member: {name}")

            if info.file_size > MAX_SINGLE:
                sys.exit(f"STOP: Oversized member: {name}")

            ratio = info.file_size / max(info.compress_size, 1)
            if info.file_size > 1024 * 1024 and ratio > 250:
                sys.exit(f"STOP: Suspicious compression ratio: {name}")

            if info.is_dir():
                continue

            digest = hashlib.sha256()
            with z.open(info, "r") as stream:
                for chunk in iter(
                    lambda: stream.read(1024 * 1024), b""
                ):
                    digest.update(chunk)

            report["files"].append({
                "path": name,
                "bytes": info.file_size,
                "sha256": digest.hexdigest()
            })

            p = PurePosixPath(name)
            if re.search(
                r"(^|/)(tests?|__tests__)/|"
                r"\.(test|spec)\.[cm]?[jt]sx?$",
                name, re.I
            ):
                report["candidate_tests"].append(name)

            if not source_candidate(name):
                continue
            if info.file_size > MAX_SCAN:
                continue

            content = z.read(info).decode("utf-8", errors="replace")

            if p.name == "package.json":
                try:
                    pkg = json.loads(content)
                    report["package_manifests"].append({
                        "path": name,
                        "name": pkg.get("name"),
                        "dependencies": pkg.get("dependencies", {}),
                        "devDependencies": pkg.get("devDependencies", {}),
                        "script_names": sorted(
                            pkg.get("scripts", {}).keys()
                        )
                    })
                except (ValueError, AttributeError):
                    report["limitations"].append(
                        f"Unreadable package manifest: {name}"
                    )

            for number, line in enumerate(content.splitlines(), 1):
                for category, pattern in PATTERNS.items():
                    matches = report["source_indicators"][category]
                    if len(matches) < 300 and re.search(
                        pattern, line, flags=re.I
                    ):
                        matches.append({
                            "path": name,
                            "line": number
                        })

    if sha256_file(archive) != before_hash:
        sys.exit("STOP: Original ZIP changed during inspection.")

    # Exclusive creation prevents overwriting an existing report.
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)

    print("Archive SHA-256:", before_hash)
    print("Files inventoried:", len(report["files"]))
    print("Candidate tests:", len(report["candidate_tests"]))
    print("Package manifests:", len(report["package_manifests"]))
    print("Report:", output)
    print("Original archive: hash unchanged")
    print("Functional test status: NOT EXECUTED")

if __name__ == "__main__":
    main()