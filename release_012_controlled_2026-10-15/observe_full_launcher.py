"""Read-only completion check for Streamlit versions that print plain URL:."""

import json
from pathlib import Path
import re
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import EVIDENCE, ROOT, digest, preserve, save


def main():
    preserve()
    original = json.loads((EVIDENCE / "full_windows_launcher.json").read_text())
    qa = Path(original["cwd"])
    text = (EVIDENCE / "full_windows_launcher.log").read_text(encoding="utf-8", errors="replace")
    tests = re.findall(r"(\d+) passed in", text)
    urls = re.findall(r"(?:Local URL:|App URL:|(?m:^\s*)URL:)\s*(http://localhost:\d+)", text)
    if "ERROR:" in text or not tests or int(tests[-1]) != 121 or not urls:
        raise RuntimeError("STOP: full normal launcher did not pass all expected stages.")
    url = urls[-1]
    with urllib.request.urlopen(url + "/_stcore/health", timeout=5) as response:
        healthy = response.status == 200 and response.read().strip() == b"ok"
    same_code = all(digest(qa / path) == value for path, value in original["source_file_digests"].items())
    if not healthy or not same_code:
        raise RuntimeError("STOP: server health or QA source digest check failed.")
    save("full_windows_launcher_observer.json", {**original, "observer": "supplementary read-only verifier; original monitor recognized Local URL/App URL but not this Streamlit version's plain URL", "url": url, "fresh_normal_launcher_test_passes": 121, "successful_full_batch_stages": ["python_check", "new_venv", "activate", "pip_upgrade_QA_only", "constrained_install", "isolated_init", "pytest", "streamlit_start"], "health_status": 200, "all_QA_source_digests_still_match_candidate": same_code, "verification_exit_code": 0, "cleanup_pending": True})
    print(json.dumps({"normal_windows_batch_tests": 121, "url": url, "health": 200, "all_QA_source_digests_match_candidate": same_code}))


if __name__ == "__main__":
    main()
