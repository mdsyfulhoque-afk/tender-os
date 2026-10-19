import streamlit as st

from ..services.ip_capture_service import add_ip_capture, export_ip_csv, list_ip
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("IP Capture")
    case = require_case(session)
    if not case:
        return
    with st.form("ip_capture"):
        col1, col2, col3 = st.columns(3)
        donor = col1.text_input("Donor", case.donor_client or "")
        sector = col2.text_input("Sector", case.sector or "")
        country = col3.text_input("Country", case.country or "")
        pattern_type = col1.text_input("Pattern type", "ToR pattern")
        confidence = col2.selectbox("Confidence", ["low", "medium", "high"], index=1)
        anonymized = col3.checkbox("Anonymized", value=True)
        title = st.text_input("Pattern title")
        description = st.text_area("Pattern description")
        reusable_asset = st.text_area("Reusable asset")
        notes = st.text_area("Notes")
        if st.form_submit_button("Capture reusable IP", type="primary"):
            add_ip_capture(session, case.case_id, donor=donor, sector=sector, country=country, pattern_type=pattern_type, confidence_level=confidence, anonymized=anonymized, pattern_title=title, pattern_description=description, reusable_asset=reusable_asset, notes=notes)
            session.commit()
            st.success("IP pattern captured.")
            st.rerun()
    if st.button("Export IP table to CSV"):
        path = export_ip_csv(session, case.case_id)
        session.commit()
        st.success(f"Exported {path}")
    show_table(list_ip(session, case.case_id), "No IP captured yet.")

