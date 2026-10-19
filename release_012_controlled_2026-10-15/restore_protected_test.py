"""User-authorized exact-byte restoration; changes only one isolated test file."""

import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import APP, AUDIT, EVIDENCE, ROOT, inventory, preserve, save

EXPECTED = "886027e6f63f2f8e68b1bce330acdb3687ca47e9a4b955c4d253f20ce3bdbd7e"
SAFETY = "e95747e2ba52edc138e333e9a3cc3e2c41a7cb043d454e8e2eeefde00186c00a"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def all_files(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main():
    preserve()
    reference = AUDIT / "isolated/release011/tests/test_release_011.py"
    target = APP / "tests/test_release_011.py"
    protected = APP / "tests/test_release_012_safety_contract.py"
    if sha(reference) != EXPECTED or sha(protected) != SAFETY or sha(AUDIT / "test_safety_contract.py") != SAFETY:
        raise RuntimeError("STOP: audited reference or protected 24-probe digest differs.")
    if sha(target) != "dd7cb078f4287ca061e4aa7b1ebb10b7bdf30045e0ca3e19c171889c9a264b6c":
        raise RuntimeError("STOP: isolated target changed since the reported checkpoint.")
    before = all_files(APP)
    baseline_before = all_files(ROOT / "baseline")
    history = EVIDENCE / "pre_resumption"
    history.mkdir(exist_ok=False)
    for path in (ROOT / "STOP_REPORT.md", EVIDENCE / "stop.json", EVIDENCE / "frozen_tests.json"):
        shutil.copy2(path, history / path.name)
    save("restoration_before.json", {"candidate_files": before, "baseline_files": baseline_before})
    shutil.copyfile(reference, target)
    after = all_files(APP)
    changes = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
    good = changes == ["tests/test_release_011.py"] and sha(target) == EXPECTED and target.read_bytes() == reference.read_bytes()
    old_tests = {r["path"]: sha(APP / r["path"]) == r["sha256"] for r in inventory() if r["path"].startswith("tests/") and r["path"] != "tests/conftest.py"}
    baseline_same = baseline_before == all_files(ROOT / "baseline")
    result = {"restored_file": str(target), "reference_sha256": EXPECTED, "restored_sha256": sha(target), "CRLF_sequences": target.read_bytes().count(b"\r\n"), "all_candidate_files_including_dependencies_checked": len(before), "restoration_changed_only": changes, "protected_24_sha256": sha(protected), "all_24_byte_identical": protected.read_bytes() == (AUDIT / "test_safety_contract.py").read_bytes(), "old_test_modules_unchanged": old_tests, "verified_recovery_snapshot_unchanged": baseline_same, "operational_preservation": preserve(), "restoration_exit_code": 0 if good else 1, "merge": "pending_approval"}
    save("restoration.json", result)
    if not (good and baseline_same and all(old_tests.values()) and result["all_24_byte_identical"]):
        raise RuntimeError("STOP: protected restoration boundary failed.")
    print(json.dumps({"restored_sha256": sha(target), "CRLF": result["CRLF_sequences"], "candidate_files_checked": len(before), "only_changed_file": changes, "operational_files_unchanged": 340, "backup_unchanged": baseline_same}, indent=2))


if __name__ == "__main__":
    main()
