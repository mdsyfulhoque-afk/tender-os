from pathlib import Path

import streamlit as st

from ..models import OutputPackage
from ..services.report_service import generate_docx_report, generate_markdown_report
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("Diagnostic Report Generator")
    case = require_case(session)
    if not case:
        return
    col1, col2 = st.columns(2)
    if col1.button("Generate Markdown report", type="primary"):
        path = generate_markdown_report(session, case.case_id)
        session.commit()
        st.success(f"Markdown report generated: {path}")
        st.rerun()
    if col2.button("Generate DOCX report"):
        path = generate_docx_report(session, case.case_id)
        session.commit()
        st.success(f"DOCX report generated: {path}")
        st.rerun()

    outputs = session.query(OutputPackage).filter(OutputPackage.case_id == case.case_id, OutputPackage.output_type.in_(["markdown_report", "docx_report"])).order_by(OutputPackage.created_at.desc()).all()
    show_table(outputs, "No reports generated yet.")
    for output in outputs:
        path = Path(output.file_path)
        if path.exists():
            st.download_button(
                f"Download {output.output_type.replace('_', ' ').title()}",
                data=path.read_bytes(),
                file_name=path.name,
                mime="text/markdown" if path.suffix == ".md" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"download_{output.output_id}",
            )
    md = next((o for o in outputs if o.output_type == "markdown_report" and Path(o.file_path).exists()), None)
    if md:
        st.markdown("### Markdown preview")
        st.markdown(Path(md.file_path).read_text(encoding="utf-8", errors="ignore"))

