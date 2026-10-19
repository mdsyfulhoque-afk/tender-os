"""Run Streamlit pages against the isolated audit application's synthetic data."""

import json
from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest

from tenderproof.db import get_session, init_db
from tenderproof.services.sample_data_service import create_demo_case


def main():
    init_db()
    with get_session() as session:
        case = create_demo_case(session)
        case_id = case.case_id
    app = AppTest.from_file(str(Path.cwd() / "app.py"))
    app.session_state["active_case_id"] = case_id
    app.run(timeout=45)
    results = []
    pages = list(app.sidebar.radio[0].options)
    for page in pages:
        app.sidebar.radio[0].set_value(page).run(timeout=45)
        results.append({"page": page, "exceptions": [str(e.message) for e in app.exception], "titles": [t.value for t in app.title]})
    Path(sys.argv[1]).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"pages": len(results), "passed": sum(not r["exceptions"] for r in results)}, indent=2))
    return int(any(r["exceptions"] for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
