import streamlit as st

from ..models import MethodologyOutline, ProposalSkeleton
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("Proposal Skeleton and Methodology")
    case = require_case(session)
    if not case:
        return
    tab1, tab2 = st.tabs(["Proposal skeleton", "Methodology outline"])
    with tab1:
        with st.form("add_skeleton"):
            col1, col2 = st.columns([1, 3])
            order = col1.number_input("Section order", min_value=1, value=1)
            title = col2.text_input("Section title")
            purpose = st.text_area("Purpose")
            inputs = st.text_area("Required inputs")
            linked = st.text_input("Linked requirements")
            if st.form_submit_button("Add skeleton section"):
                session.add(ProposalSkeleton(case_id=case.case_id, section_order=int(order), section_title=title, purpose=purpose, required_inputs=inputs, linked_requirements=linked))
                session.commit()
                st.success("Proposal section added.")
                st.rerun()
        show_table(session.query(ProposalSkeleton).filter(ProposalSkeleton.case_id == case.case_id).order_by(ProposalSkeleton.section_order).all(), "No proposal skeleton sections.")
    with tab2:
        with st.form("add_methodology"):
            col1, col2 = st.columns([1, 3])
            order = col1.number_input("Module order", min_value=1, value=1)
            title = col2.text_input("Module title")
            description = st.text_area("Module description")
            linked = st.text_input("Linked requirements")
            evidence = st.text_area("Evidence needed")
            conditions = st.text_area(
                "Data collection conditions",
                help="Record access, consent, safeguarding, language, sampling, seasonality, connectivity, and respondent availability constraints.",
            )
            approach = st.selectbox(
                "Analysis approach",
                ["Human-led", "Rules-based NLP (local)", "SLM-assisted NLP (external model)"],
                help="This records the planned approach. SLM-assisted NLP is a planning label only; no language model is connected in this local MVP.",
            )
            if st.form_submit_button("Add methodology module"):
                session.add(MethodologyOutline(case_id=case.case_id, module_order=int(order), module_title=title, module_description=description, linked_requirements=linked, evidence_needed=evidence, data_collection_conditions=conditions, analysis_approach=approach))
                session.commit()
                st.success("Methodology module added.")
                st.rerun()
        show_table(session.query(MethodologyOutline).filter(MethodologyOutline.case_id == case.case_id).order_by(MethodologyOutline.module_order).all(), "No methodology modules.")

