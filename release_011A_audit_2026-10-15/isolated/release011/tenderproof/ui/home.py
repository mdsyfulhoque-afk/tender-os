import streamlit as st

from ..models import AuditEvent, Case, GapItem, Source
from ..services.sample_data_service import create_demo_case
from .helpers import case_selector, rows_to_df, set_active_case


def render(session) -> None:
    st.title("TenderProof OS / ProposalGuard")
    st.subheader("AI-assisted donor tender diagnostic command center")
    col1, col2, col3, col4 = st.columns(4)
    total_cases = session.query(Case).count()
    open_gaps = session.query(GapItem).filter(GapItem.status != "closed").count()
    sources = session.query(Source).count()
    packaged = session.query(Case).filter(Case.readiness_label == "EXPORT_READY").count()
    col1.metric("Cases", total_cases)
    col2.metric("Open gaps", open_gaps)
    col3.metric("Sources", sources)
    col4.metric("Export-ready", packaged)

    st.divider()
    left, right = st.columns([1, 2])
    with left:
        st.markdown("### Quick actions")
        if st.button("Create demo case", type="primary"):
            case = create_demo_case(session)
            set_active_case(case.case_id)
            session.commit()
            st.success(f"Demo case opened or created: {case.case_id}")
            st.rerun()
        case_selector(session)
    with right:
        st.markdown("### Upcoming deadlines")
        rows = session.query(Case).filter(Case.submission_deadline != "").order_by(Case.submission_deadline.asc()).limit(10).all()
        if rows:
            st.dataframe(rows_to_df(rows)[["case_id", "client_name", "tender_title", "submission_deadline", "readiness_label"]], use_container_width=True, hide_index=True)
        else:
            st.info("No deadlines recorded.")

    st.markdown("### Latest audit events")
    events = session.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(12).all()
    if events:
        st.dataframe(rows_to_df(events)[["created_at", "case_id", "event_type", "event_message"]], use_container_width=True, hide_index=True)
    else:
        st.info("No audit events yet.")
