import streamlit as st

from ..services.gap_service import list_gaps, sync_gaps_from_compliance, sync_gaps_from_cv
from ..services.risk_service import add_risk, auto_generate_risks_from_gaps, list_risks
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("Risk Register and Gaps")
    case = require_case(session)
    if not case:
        return
    col1, col2, col3 = st.columns(3)
    if col1.button("Sync compliance gaps"):
        sync_gaps_from_compliance(session, case.case_id)
        session.commit()
        st.success("Compliance gaps synced.")
        st.rerun()
    if col2.button("Sync CV gaps"):
        sync_gaps_from_cv(session, case.case_id)
        session.commit()
        st.success("CV gaps synced.")
        st.rerun()
    if col3.button("Auto-generate risks from gaps", type="primary"):
        created = auto_generate_risks_from_gaps(session, case.case_id)
        session.commit()
        st.success(f"Created {len(created)} risks.")
        st.rerun()

    with st.expander("Add risk manually"):
        with st.form("add_risk"):
            risk_category = st.text_input("Risk category", "compliance")
            description = st.text_area("Risk description")
            col1, col2, col3 = st.columns(3)
            severity = col1.selectbox("Severity", ["low", "medium", "high", "critical"], index=1)
            likelihood = col2.selectbox("Likelihood", ["low", "medium", "high", "critical"], index=1)
            owner = col3.text_input("Owner")
            mitigation = st.text_area("Mitigation")
            if st.form_submit_button("Add risk"):
                add_risk(session, case.case_id, risk_category=risk_category, risk_description=description, severity=severity, likelihood=likelihood, owner=owner, mitigation=mitigation)
                session.commit()
                st.success("Risk added.")
                st.rerun()

    st.markdown("### Gap items")
    show_table(list_gaps(session, case.case_id), "No gaps recorded.")
    st.markdown("### Risk register")
    show_table(list_risks(session, case.case_id), "No risks recorded.")

