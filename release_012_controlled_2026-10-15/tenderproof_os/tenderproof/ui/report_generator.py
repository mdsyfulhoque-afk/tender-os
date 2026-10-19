from pathlib import Path

import streamlit as st

from ..models import OutputPackage
from ..services.report_service import generate_docx_report, generate_markdown_report
from ..services.decision_service import file_hash, output_is_current, release_context
from .helpers import require_case, rows_to_df


def render(session) -> None:
    st.title("Diagnostic Report Generator")
    case = require_case(session)
    if not case:
        return
    context = release_context(session, case.case_id)
    st.write(f"Current release: {context['readiness_label']}")
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
    if outputs:
        table = rows_to_df(outputs).drop(columns=["readiness_label", "verification_status"])
        table["current_release"] = [o.readiness_label if output_is_current(o, context["snapshot_hash"], context["approval"]) and context["approved"] else "DRAFT / HISTORICAL" for o in outputs]
        st.dataframe(table, hide_index=True)
    for output in outputs:
        path = Path(output.file_path)
        if path.exists():
            st.download_button(
                f"Download {output.output_type.replace('_', ' ').title()} / {output.output_id}",
                data=path.read_bytes(),
                file_name=path.name,
                mime="text/markdown" if path.suffix == ".md" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"download_{output.output_id}",
                disabled=not output.content_sha256 or file_hash(path) != output.content_sha256 or (bool(output.readiness_label in {"CLIENT_READY", "EXPORT_READY"} or output.approval_id) and not (context["approved"] and output_is_current(output, context["snapshot_hash"], context["approval"]))),
            )
    md = next((o for o in outputs if o.output_type == "markdown_report" and o.snapshot_hash == context["snapshot_hash"] and o.verification_status != "stale" and o.content_sha256 and file_hash(o.file_path) == o.content_sha256 and (not o.approval_id or (context["approved"] and output_is_current(o, context["snapshot_hash"], context["approval"])))), None)
    if md:
        st.markdown("### Markdown preview")
        st.markdown(Path(md.file_path).read_text(encoding="utf-8", errors="ignore"))

