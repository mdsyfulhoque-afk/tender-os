import streamlit as st

from ..models import NormalizedRequirement
from ..services.extraction_service import add_manual_requirement, create_requirements_from_source, list_requirements, update_requirement
from ..services.source_service import list_sources
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("ToR Extraction")
    case = require_case(session)
    if not case:
        return
    sources = list_sources(session, case.case_id)
    if sources:
        source_id = st.selectbox("Source for extraction", [s.source_id for s in sources], format_func=lambda sid: f"{sid} - {next(s.filename for s in sources if s.source_id == sid)}")
        if st.button("Create requirements from selected source", type="primary"):
            created = create_requirements_from_source(session, case.case_id, source_id)
            session.commit()
            st.success(f"Created {len(created)} new requirement rows.")
            st.rerun()
    else:
        st.info("Register a source or paste manual ToR text first.")

    with st.expander("Add requirement manually", expanded=False):
        with st.form("manual_req"):
            text = st.text_area("Atomic requirement text")
            col1, col2, col3 = st.columns(3)
            category = col1.text_input("Category", "technical requirement")
            section = col2.text_input("ToR section/page", "manual")
            risk = col3.selectbox("Risk level", ["low", "medium", "high", "critical"], index=1)
            mandatory = st.checkbox("Mandatory", value=True)
            evidence = st.text_area("Evidence needed")
            if st.form_submit_button("Add manual requirement"):
                add_manual_requirement(session, case.case_id, requirement_text=text, requirement_category=category, tor_section_page=section, mandatory=mandatory, evidence_needed=evidence, risk_level=risk)
                session.commit()
                st.success("Requirement added.")
                st.rerun()

    st.markdown("### Normalized requirements")
    rows = list_requirements(session, case.case_id)
    if rows:
        with st.expander("Edit existing requirement", expanded=False):
            requirement_id = st.selectbox("Requirement", [r.requirement_id for r in rows], format_func=lambda rid: f"{rid} - {next(r.atomic_requirement_text[:80] for r in rows if r.requirement_id == rid)}")
            req = next(r for r in rows if r.requirement_id == requirement_id)
            with st.form("edit_requirement"):
                text = st.text_area("Atomic requirement text", req.atomic_requirement_text or req.requirement_text)
                col1, col2, col3 = st.columns(3)
                category = col1.text_input("Category", req.requirement_category or "")
                section = col2.text_input("ToR section/page", req.tor_section_page or "")
                risk = col3.selectbox("Risk level", ["low", "medium", "high", "critical"], index=["low", "medium", "high", "critical"].index(req.risk_level) if req.risk_level in ["low", "medium", "high", "critical"] else 1)
                mandatory = st.checkbox("Mandatory", value=bool(req.mandatory))
                needs_review = st.checkbox("Needs review", value=bool(req.needs_review))
                evidence = st.text_area("Evidence needed", req.evidence_needed or "")
                proposal_section = st.text_input("Proposal section affected", req.proposal_section_affected or "")
                notes = st.text_area("Notes", req.notes or "")
                if st.form_submit_button("Save requirement changes"):
                    update_requirement(session, requirement_id, atomic_requirement_text=text, requirement_text=text, requirement_category=category, tor_section_page=section, risk_level=risk, mandatory=mandatory, needs_review=needs_review, evidence_needed=evidence, proposal_section_affected=proposal_section, notes=notes)
                    session.commit()
                    st.success("Requirement updated; match_key recalculated.")
                    st.rerun()
    show_table(rows, "No requirements extracted yet.")
