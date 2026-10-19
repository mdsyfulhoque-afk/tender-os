import streamlit as st
from pathlib import Path

from ..config import REFERENCE_DIR
from ..services.egp_service import ensure_egp_checklist, update_egp_checklist
from .helpers import require_case


STAGES = {
    "Registration": "registration",
    "Tender opportunity": "opportunity",
    "Preparation and submission": ("preparation", "submission", "rules"),
    "Post-award": "post_award",
}
STATUSES = ["Pending Input", "Met", "Gap", "Not Applicable"]


def render(session) -> None:
    st.title("Bangladesh e-GP Readiness")
    case = require_case(session)
    if not case:
        return
    st.info(
        "Internal bidder-side readiness aid only. It does not log into or submit through e-GP, determine legal eligibility, or replace the live tender document and current BPPA instructions."
    )
    st.markdown(
        "Current references: [Bangladesh e-GP portal](https://www.eprocure.gov.bd/) · "
        "[BPPA rules and procedures](https://www.bppa.gov.bd/procurement-policy-and-procedure-documents/procurement-rules.html) · "
        "[PPR 2025 effective notice](https://www.bppa.gov.bd/media-communication/news-1517.html) · "
        "[Rule 154 clarification](https://www.bppa.gov.bd/media-communication/news-1524.html) · "
        "[e-GP Guidelines (Revised) 2025](https://www.eprocure.gov.bd/help/guidelines/eGP_Guidelines.pdf) · "
        "[Registration documents](https://www.eprocure.gov.bd/MandRegDoc.jsp)"
    )
    st.caption("Sources checked 12 Oct 2026. The 2025 e-GP operational guideline and PPR 2025 are separate references; confirm the applicable law, transition and amendments for each tender.")
    ocr_path = REFERENCE_DIR / "e_gp_tender_book_ocr.txt"
    if ocr_path.exists():
        st.download_button(
            "Download searchable OCR of supplied e-GP guide",
            data=ocr_path.read_bytes(),
            file_name=ocr_path.name,
            mime="text/plain",
        )

    items = ensure_egp_checklist(session, case.case_id)
    done = sum(item.status in {"Met", "Not Applicable"} for item in items)
    st.progress(done / len(items), text=f"{done} of {len(items)} checks resolved")

    for title, stage_filter in STAGES.items():
        stage_values = (stage_filter,) if isinstance(stage_filter, str) else stage_filter
        group = [item for item in items if item.stage in stage_values]
        with st.expander(title, expanded=title in {"Registration", "Tender opportunity"}):
            with st.form(f"egp_{stage_values[0]}"):
                updates = []
                for item in group:
                    st.markdown(f"**{item.item_title}**")
                    st.caption(item.guidance)
                    col_status, col_evidence = st.columns([1, 2])
                    status = col_status.selectbox(
                        "Status",
                        STATUSES,
                        index=STATUSES.index(item.status) if item.status in STATUSES else 0,
                        key=f"egp_status_{item.item_key}",
                    )
                    note = col_evidence.text_input(
                        "Evidence / reference",
                        value=item.evidence_notes or "",
                        key=f"egp_note_{item.item_key}",
                    )
                    updates.append({"item_key": item.item_key, "status": status, "evidence_notes": note})
                if st.form_submit_button(f"Save {title.lower()}"):
                    update_egp_checklist(session, case.case_id, updates)
                    session.commit()
                    st.success("Checklist saved.")
                    st.rerun()
