import streamlit as st

from ..models import OutputPackage
from ..services.export_service import REQUIRED_SHEETS, export_case_to_excel
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("Excel Export")
    case = require_case(session)
    if not case:
        return
    st.markdown("Workbook sheets: " + ", ".join(REQUIRED_SHEETS))
    if st.button("Generate Excel workbook", type="primary"):
        path = export_case_to_excel(session, case.case_id)
        session.commit()
        st.success(f"Excel workbook generated: {path}")
        st.rerun()
    outputs = session.query(OutputPackage).filter(OutputPackage.case_id == case.case_id, OutputPackage.output_type == "excel_export").all()
    show_table(outputs, "No Excel exports yet.")

