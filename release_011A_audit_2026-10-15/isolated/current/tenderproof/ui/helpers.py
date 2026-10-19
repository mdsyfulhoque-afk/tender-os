import pandas as pd
import streamlit as st

from ..models import Case
from ..services.case_service import get_case, list_cases


def active_case_id() -> str | None:
    return st.session_state.get("active_case_id")


def set_active_case(case_id: str) -> None:
    st.session_state["active_case_id"] = case_id


def current_case(session) -> Case | None:
    return get_case(session, active_case_id())


def require_case(session) -> Case | None:
    case = current_case(session)
    if not case:
        st.warning("Create or open a diagnostic case first.")
        return None
    st.caption(f"Active case: {case.case_id} | {case.client_name or 'Client pending'} | {case.readiness_label}")
    return case


def case_selector(session) -> Case | None:
    cases = list_cases(session)
    if not cases:
        st.info("No cases yet. Create a case or load demo data.")
        return None
    ids = [case.case_id for case in cases]
    current = active_case_id()
    index = ids.index(current) if current in ids else 0
    selected = st.selectbox("Open case", ids, index=index, format_func=lambda cid: _case_label(cases, cid))
    set_active_case(selected)
    return get_case(session, selected)


def _case_label(cases, case_id: str) -> str:
    case = next((item for item in cases if item.case_id == case_id), None)
    if not case:
        return case_id
    return f"{case.case_id} - {case.client_name} - {case.tender_title}"


def rows_to_df(rows) -> pd.DataFrame:
    data = []
    for row in rows:
        data.append({c.name: getattr(row, c.name) for c in row.__table__.columns})
    return pd.DataFrame(data)


def show_table(rows, empty_message: str = "No rows yet.") -> None:
    if not rows:
        st.info(empty_message)
        return
    st.dataframe(rows_to_df(rows), use_container_width=True, hide_index=True)

