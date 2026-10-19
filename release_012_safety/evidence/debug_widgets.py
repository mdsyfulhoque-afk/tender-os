from pathlib import Path
from streamlit.testing.v1 import AppTest
from tenderproof.db import get_session
from tenderproof.models import Case

with get_session() as session:
    case_id = session.query(Case).first().case_id
app = AppTest.from_file(str(Path.cwd() / "app.py"))
app.session_state["active_case_id"] = case_id
app.run(timeout=40)
app.sidebar.radio[0].set_value("Verification / Audit Log").run(timeout=40)
for category in ("date_input", "text_input", "text_area", "checkbox", "button", "selectbox", "radio"):
    for item in getattr(app, category):
        try:
            prop = next(cls.__dict__["_widget_state"] for cls in type(item).__mro__ if "_widget_state" in cls.__dict__)
            prop.fget(item)
        except Exception as exc:
            print(category, item.label, type(exc).__name__, str(exc))
