import streamlit as st

from ..services.bid_score_service import ensure_scorecard_categories, latest_recommendation, save_scores_and_recommendation
from ..services.decision_service import release_context
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("Bid/No-Bid Scorecard")
    case = require_case(session)
    if not case:
        return
    rows = ensure_scorecard_categories(session, case.case_id)
    session.commit()
    with st.form("scorecard"):
        scores = {}
        for row in rows:
            st.markdown(f"**{row.category.title()}**")
            col1, col2 = st.columns([1, 4])
            score = col1.slider("Score", 0, row.max_score or 5, row.score or 0, key=f"score_{row.id}")
            rationale = col2.text_input("Rationale", row.rationale or "", key=f"rat_{row.id}")
            evidence = st.text_input("Evidence or gap reference", row.evidence_or_gap_reference or "", key=f"ev_{row.id}")
            scores[row.category] = {"score": score, "rationale": rationale, "evidence_or_gap_reference": evidence}
        if st.form_submit_button("Save scores and generate recommendation", type="primary"):
            rec = save_scores_and_recommendation(session, case.case_id, scores)
            session.commit()
            st.success(f"Recommendation: {rec.recommendation} ({rec.percentage}%)")
            st.rerun()

    rec = latest_recommendation(session, case.case_id)
    if rec:
        context = release_context(session, case.case_id)
        a, b, c = st.columns(3)
        a.metric("Opportunity score", f"{rec.percentage}%")
        b.metric("Mandatory eligibility", context["eligibility"])
        c.metric("Release clearance", "Approved" if context["approved"] else "Pending / blocked")
        st.write(f"Provisional opportunity recommendation: {rec.recommendation}")
    st.markdown("### Scorecard rows")
    show_table(rows, "No score rows.")

