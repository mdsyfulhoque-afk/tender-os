import streamlit as st

from ..models import AuditEvent, VerificationResult
from ..services.verification_service import run_verification
from .helpers import require_case, rows_to_df, show_table


def render(session) -> None:
    st.title("Verification / Audit Log")
    case = require_case(session)
    if not case:
        return
    if st.button("Run verification", type="primary"):
        summary = run_verification(session, case.case_id)
        session.commit()
        st.success(f"Verification: {summary.overall_status}; readiness: {summary.readiness_label}")
        st.rerun()
    results = session.query(VerificationResult).filter(VerificationResult.case_id == case.case_id).order_by(VerificationResult.id).all()
    if results:
        blockers = [r for r in results if r.blocker and r.status != "passed"]
        warnings = [r for r in results if r.status == "warning"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Blockers", len(blockers))
        col2.metric("Warnings", len(warnings))
        col3.metric("Readiness", case.readiness_label)
    st.markdown("### Verification results")
    show_table(results, "No verification run yet.")
    st.markdown("### Audit events")
    events = session.query(AuditEvent).filter(AuditEvent.case_id == case.case_id).order_by(AuditEvent.created_at.desc()).limit(100).all()
    show_table(events, "No audit events for this case.")

