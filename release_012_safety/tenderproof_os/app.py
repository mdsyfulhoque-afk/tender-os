import streamlit as st

from tenderproof.config import DB_PATH, ensure_directories
from tenderproof.db import get_session, init_db
from tenderproof.services.sample_data_service import create_seed_csvs
from tenderproof.ui import (
    bid_scorecard,
    cases,
    compliance,
    cv_matcher,
    exports,
    egp_readiness,
    home,
    intake,
    ip_capture,
    proposal_methodology,
    report_generator,
    risks_gaps,
    settings,
    tor_extraction,
    verification,
    workflow_optimizer,
)


PAGES = {
    "Home / Command Center": home.render,
    "Workflow Optimizer": workflow_optimizer.render,
    "Bangladesh e-GP Readiness": egp_readiness.render,
    "Create or Open Case": cases.render,
    "Upload / Register Inputs": intake.render,
    "ToR Extraction": tor_extraction.render,
    "Compliance Matrix": compliance.render,
    "CV Matcher": cv_matcher.render,
    "Bid/No-Bid Scorecard": bid_scorecard.render,
    "Risk Register and Gaps": risks_gaps.render,
    "Proposal Skeleton and Methodology": proposal_methodology.render,
    "Diagnostic Report Generator": report_generator.render,
    "Excel Export": exports.render,
    "IP Capture": ip_capture.render,
    "Verification / Audit Log": verification.render,
    "Settings": settings.render,
}


def main() -> None:
    st.set_page_config(page_title="TenderProof OS / ProposalGuard", layout="wide")
    ensure_directories()
    init_db()
    create_seed_csvs()

    st.sidebar.title("TenderProof OS")
    st.sidebar.caption("ProposalGuard local MVP")
    page_name = st.sidebar.radio("Workspace", list(PAGES.keys()), key="workspace_page")
    st.sidebar.divider()
    st.sidebar.caption(f"DB: {DB_PATH}")

    with get_session() as session:
        PAGES[page_name](session)


if __name__ == "__main__":
    main()

