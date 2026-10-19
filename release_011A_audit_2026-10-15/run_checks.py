"""Run all audit checks in disposable copies; retain stdout and JUnit evidence."""

import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


OUT = Path(__file__).resolve().parent
PYTHON = OUT.parent / "tenderproof_os" / ".venv" / "Scripts" / "python.exe"


def main():
    (OUT / "test_results").mkdir(exist_ok=True)
    results = []
    for label in ("current", "release011"):
        root = OUT / "isolated" / label
        env = {**os.environ, "PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONUTF8": "1", "TENDERPROOF_DB_PATH": str(root / "storage" / "tenderproof.db")}
        for suite, target in (("regression", "tests"), ("safety", str(OUT / "test_safety_contract.py"))):
            name = f"{label}_{suite}"
            junit = OUT / "test_results" / f"{name}.xml"
            args = [str(PYTHON), "-B", "-m", "pytest", target, "-q", "--tb=short", "-p", "no:cacheprovider", f"--junitxml={junit}"]
            result = subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            (OUT / "test_results" / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
            xml = ET.parse(junit).getroot()
            cases = [{"name": n.attrib["name"], "result": "failed" if n.find("failure") is not None else "error" if n.find("error") is not None else "skipped" if n.find("skipped") is not None else "passed"} for n in xml.iter("testcase")]
            item = {"target": label, "suite": suite, "exit_code": result.returncode, "tests": len(cases), "passed": sum(c["result"] == "passed" for c in cases), "failed": sum(c["result"] == "failed" for c in cases), "errors": sum(c["result"] == "error" for c in cases), "cases": cases, "command": args}
            results.append(item)
            print(json.dumps({k: v for k, v in item.items() if k not in {"cases", "command"}}), flush=True)
        args = [str(PYTHON), "-B", str(OUT / "ui_smoke.py"), str(OUT / "test_results" / f"{label}_ui.json")]
        ui = subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        (OUT / "test_results" / f"{label}_ui.log").write_text(ui.stdout + ui.stderr, encoding="utf-8")
        results.append({"target": label, "suite": "ui_smoke", "exit_code": ui.returncode})
        print(f"{label} UI smoke exit: {ui.returncode}", flush=True)
    (OUT / "test_results" / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
