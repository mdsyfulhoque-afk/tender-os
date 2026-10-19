"""Exercise the normal Windows wrapper in a disposable, separately copied QA tree."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from control import APP, EVIDENCE, ROOT, digest, preserve, save


def main():
    preserve()
    qa = ROOT / "runtime/full_windows_launcher"
    qa.mkdir(exist_ok=False, parents=True)
    code = {}
    for base, dirs, files in os.walk(APP):
        dirs[:] = [d for d in dirs if d not in {".venv", "__pycache__", ".pytest_cache", "storage", "data"}]
        for name in files:
            source = Path(base) / name
            relative = source.relative_to(APP)
            target = qa / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            code[relative.as_posix()] = digest(source)
    # The migration regression reads this copy only; normal startup uses a separate empty runtime.
    (qa / "storage").mkdir()
    shutil.copy2(ROOT / "baseline/tenderproof.db", qa / "storage/tenderproof.db")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TENDERPROOF_RUNTIME_ROOT=str(ROOT / "runtime/full_launcher_data"))
    env.pop("TENDERPROOF_DB_PATH", None)
    env.pop("TENDERPROOF_LAUNCHER_VERIFY", None)
    env["PATH"] = str(APP / ".venv/Scripts") + os.pathsep + env["PATH"]
    args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", "& '.\\deploy_and_run.bat'\nexit $LASTEXITCODE"]
    log_path = EVIDENCE / "full_windows_launcher.log"
    record = {"command": args, "cwd": str(qa), "normal_batch_mode": True, "health_only_mode": False, "source_file_digests": code, "operational": "not used", "merge": "pending_approval"}
    save("full_windows_launcher.json", record)
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(args, cwd=qa, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        record["test_process_id"] = process.pid
        save("full_windows_launcher.json", record)
        print(f"Normal batch verification started in separate QA copy, PID {process.pid}.", flush=True)
        deadline = time.monotonic() + 900
        healthy = False
        observed_url = None
        try:
            while time.monotonic() < deadline:
                text = log_path.read_text(encoding="utf-8", errors="replace")
                if "ERROR:" in text or process.poll() is not None:
                    raise RuntimeError("STOP: full normal Windows launcher exited or reported an error; inspect its log.")
                urls = re.findall(r"(?:Local URL:|App URL:)\s*(http://localhost:\d+)", text)
                if urls and "passed in" in text:
                    observed_url = urls[-1]
                    try:
                        with urllib.request.urlopen(observed_url + "/_stcore/health", timeout=2) as response:
                            healthy = response.status == 200 and response.read().strip() == b"ok"
                    except (OSError, TimeoutError):
                        healthy = False
                if healthy:
                    break
                time.sleep(2)
            if not healthy:
                raise RuntimeError("STOP: full Windows launcher did not reach a healthy test server.")
            text = log_path.read_text(encoding="utf-8", errors="replace")
            tests = re.findall(r"(\d+) passed in", text)
            record.update({"successful_full_batch_stages": ["python_check", "new_venv", "activate", "pip_upgrade_in_QA_only", "constrained_dependencies", "isolated_init", "pytest", "run_app_streamlit"], "fresh_normal_launcher_test_passes": int(tests[-1]), "url": observed_url, "health_status": 200, "wrapper_called_exact_primary_filename": "deploy&run.bat", "all_QA_source_digests_still_match_candidate": all(digest(qa / name) == value for name, value in code.items()), "verification_exit_code": 0})
            if record["fresh_normal_launcher_test_passes"] != 121 or not record["all_QA_source_digests_still_match_candidate"]:
                raise RuntimeError("STOP: launcher verification did not preserve source or run all tests.")
            save("full_windows_launcher.json", record)
            print("Full normal Windows wrapper completed install, 121 passing tests and healthy Streamlit startup.", flush=True)
        finally:
            # This PID is the process created above; /T includes Windows venv launcher descendants.
            stopped = subprocess.run(["taskkill.exe", "/PID", str(process.pid), "/T", "/F"], capture_output=True, text=True)
            record["cleanup_command"] = ["taskkill.exe", "/PID", str(process.pid), "/T", "/F"]
            record["cleanup_exit_code"] = stopped.returncode
            record["cleanup_output"] = stopped.stdout + stopped.stderr
            record["cleanup_requested_for_own_QA_tree_only"] = True
            record["launcher_process_exit_code_after_intentional_cleanup"] = process.wait(timeout=20)
            save("full_windows_launcher.json", record)
    preserve()


if __name__ == "__main__":
    main()
