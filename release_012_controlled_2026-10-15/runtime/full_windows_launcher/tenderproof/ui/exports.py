import streamlit as st
from pathlib import Path

from ..models import OutputPackage
from ..services.export_service import REQUIRED_SHEETS, export_case_to_excel
from ..services.decision_service import file_hash, output_is_current, release_context
from .helpers import require_case, rows_to_df


def render(session) -> None:
    st.title("Excel Export")
    case = require_case(session)
    if not case:
        return
    context = release_context(session, case.case_id)
    st.write(f"Current release: {context['readiness_label']}")
    if st.button("Generate Excel workbook", type="primary"):
        path = export_case_to_excel(session, case.case_id)
        session.commit()
        st.success(f"Excel workbook generated: {path}")
        st.rerun()
    outputs = session.query(OutputPackage).filter(OutputPackage.case_id == case.case_id, OutputPackage.output_type == "excel_export").all()
    if outputs:
        table = rows_to_df(outputs).drop(columns=["readiness_label", "verification_status"])
        table["current_release"] = [o.readiness_label if context["approved"] and output_is_current(o, context["snapshot_hash"], context["approval"]) else "DRAFT / HISTORICAL" for o in outputs]
        st.dataframe(table, hide_index=True)
    for output in outputs:
        path = Path(output.file_path)
        if path.is_file():
            current = context["approved"] and output_is_current(output, context["snapshot_hash"], context["approval"])
            st.download_button(f"Download workbook / {output.output_id}", path.read_bytes(), file_name=path.name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"xlsx_{output.output_id}", disabled=not output.content_sha256 or file_hash(path) != output.content_sha256 or (bool(output.approval_id or output.readiness_label in {"CLIENT_READY", "EXPORT_READY"}) and not current))

