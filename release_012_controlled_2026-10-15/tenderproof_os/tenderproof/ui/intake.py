import streamlit as st

from ..services.source_service import get_source_text, list_sources, register_manual_text, save_uploaded_file
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("Upload / Register Inputs")
    case = require_case(session)
    if not case:
        return
    uploaded = st.file_uploader("Upload ToR/source document", type=["pdf", "docx", "txt"])
    source_category = st.selectbox("Source category", ["ToR", "Annex", "CV", "Clarification", "Manual ToR Text"])
    if uploaded and st.button("Save and extract uploaded file", type="primary"):
        with st.status("Saving and extracting source...", expanded=True) as status:
            progress = st.progress(0, text="Checking document text layer...")

            def update_ocr_progress(current, total):
                progress.progress(current / total, text=f"OCR page {current} of {total}")

            source = save_uploaded_file(session, case.case_id, uploaded, source_category, update_ocr_progress)
            progress.empty()
            status.update(label=f"Source processed: {source.extraction_status}", state="complete", expanded=False)
        session.commit()
        st.success(f"Saved source {source.source_id}; extraction status: {source.extraction_status}")
        st.rerun()

    st.markdown("### Manual ToR text")
    with st.form("manual_tor"):
        text = st.text_area("Paste ToR text", height=220)
        if st.form_submit_button("Register manual ToR text"):
            source = register_manual_text(session, case.case_id, text)
            session.commit()
            st.success(f"Registered manual source {source.source_id}")
            st.rerun()

    st.markdown("### Sources")
    sources = list_sources(session, case.case_id)
    show_table(sources, "No sources registered.")
    if sources:
        source_id = st.selectbox("Preview extracted text", [s.source_id for s in sources], format_func=lambda sid: f"{sid} - {next(s.filename for s in sources if s.source_id == sid)}")
        source = next(s for s in sources if s.source_id == source_id)
        st.text_area("Extraction preview", get_source_text(source)[:8000], height=260)
