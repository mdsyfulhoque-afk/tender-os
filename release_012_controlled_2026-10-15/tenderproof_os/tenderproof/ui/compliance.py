import streamlit as st

from ..constants import COMPLIANCE_STATUSES
from ..services.compliance_service import auto_create_compliance_rows, list_compliance, update_compliance_row
from ..services.gap_service import sync_gaps_from_compliance
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("Compliance Matrix")
    case = require_case(session)
    if not case:
        return
    col1, col2 = st.columns(2)
    if col1.button("Auto-create compliance rows", type="primary"):
        rows = auto_create_compliance_rows(session, case.case_id)
        session.commit()
        st.success(f"Created {len(rows)} rows and synced gaps.")
        st.rerun()
    if col2.button("Sync GapItems from compliance"):
        rows = sync_gaps_from_compliance(session, case.case_id)
        session.commit()
        st.success(f"Synced {len(rows)} compliance gap rows.")
        st.rerun()

    rows = list_compliance(session, case.case_id)
    if rows:
        compliance_id = st.selectbox("Edit compliance row", [row.compliance_id for row in rows], format_func=lambda cid: f"{cid} - {next(r.requirement_id for r in rows if r.compliance_id == cid)}")
        row = next(r for r in rows if r.compliance_id == compliance_id)
        with st.form("edit_compliance"):
            status = st.selectbox("Status", COMPLIANCE_STATUSES, index=COMPLIANCE_STATUSES.index(row.status) if row.status in COMPLIANCE_STATUSES else 3)
            available_evidence = st.text_area("Available evidence", row.available_evidence or "")
            gap = st.text_area("Gap", row.gap or "")
            action = st.text_area("Action required", row.action_required or "")
            owner = st.text_input("Responsible person", row.responsible_person or "")
            risk = st.selectbox("Risk level", ["low", "medium", "high", "critical"], index=["low", "medium", "high", "critical"].index(row.risk_level) if row.risk_level in ["low", "medium", "high", "critical"] else 1)
            if st.form_submit_button("Save compliance row"):
                update_compliance_row(session, compliance_id, status=status, available_evidence=available_evidence, gap=gap, action_required=action, responsible_person=owner, risk_level=risk)
                session.commit()
                st.success("Compliance row saved and gaps synced.")
                st.rerun()

    st.markdown("### Compliance ledger")
    show_table(rows, "No compliance rows yet.")

