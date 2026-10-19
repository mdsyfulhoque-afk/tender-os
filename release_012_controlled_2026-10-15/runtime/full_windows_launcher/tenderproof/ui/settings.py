import streamlit as st

from ..config import DB_PATH, EXTRACTED_TEXT_DIR, EXPORTS_DIR, REPORTS_DIR, STORAGE_DIR, UPLOADS_DIR, ensure_directories
from ..db import init_db
from ..services.sample_data_service import create_demo_case, create_seed_csvs
from .helpers import set_active_case


def render(session) -> None:
    st.title("Settings")
    st.markdown("### Local paths")
    st.write(
        {
            "database": str(DB_PATH),
            "storage": str(STORAGE_DIR),
            "uploads": str(UPLOADS_DIR),
            "extracted_text": str(EXTRACTED_TEXT_DIR),
            "reports": str(REPORTS_DIR),
            "exports": str(EXPORTS_DIR),
        }
    )
    col1, col2, col3 = st.columns(3)
    if col1.button("Ensure folders"):
        ensure_directories()
        st.success("Folders verified.")
    if col2.button("Initialize database"):
        init_db()
        st.success("Database initialized.")
    if col3.button("Create / refresh seed CSVs"):
        create_seed_csvs()
        st.success("Seed CSVs created.")
    if st.button("Create demo case", type="primary"):
        case = create_demo_case(session)
        set_active_case(case.case_id)
        session.commit()
        st.success(f"Created demo case {case.case_id}")
        st.rerun()

