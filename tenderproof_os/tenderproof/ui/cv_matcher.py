import streamlit as st

from ..services.cv_match_service import add_cv_match, list_cv_matches
from ..services.extraction_service import list_requirements
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("CV Matcher")
    case = require_case(session)
    if not case:
        return
    reqs = list_requirements(session, case.case_id)
    req_options = [""] + [r.requirement_id for r in reqs]
    with st.form("add_cv"):
        col1, col2, col3 = st.columns(3)
        requirement_id = col1.selectbox("Linked requirement", req_options)
        expert_role = col2.text_input("Expert role")
        candidate_name = col3.text_input("Candidate name")
        required_years = col1.text_input("Required years")
        score = col2.slider("Match score", 1, 5, 3)
        rewrite_needed = col3.checkbox("Rewrite needed")
        required_qualification = st.text_area("Required qualification")
        cv_evidence = st.text_area("CV evidence actually provided")
        gap = st.text_area("Gap")
        if st.form_submit_button("Add CV match", type="primary"):
            add_cv_match(
                session,
                case.case_id,
                requirement_id=requirement_id,
                expert_role=expert_role,
                candidate_name=candidate_name,
                required_years=required_years,
                required_qualification=required_qualification,
                cv_evidence=cv_evidence,
                match_score_1_to_5=score,
                rewrite_needed=rewrite_needed,
                gap=gap,
            )
            session.commit()
            st.success("CV match added. Suggested language uses provided evidence only.")
            st.rerun()

    st.markdown("### CV matches")
    show_table(list_cv_matches(session, case.case_id), "No CV matches yet.")

