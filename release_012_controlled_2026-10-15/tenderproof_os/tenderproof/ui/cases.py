import streamlit as st

from ..constants import CASE_STATUSES
from ..services.case_service import create_case, update_case
from .helpers import case_selector, current_case, rows_to_df, set_active_case


def render(session) -> None:
    st.title("Create or Open Case")
    tab_create, tab_open = st.tabs(["Create case", "Open / update case"])
    with tab_create:
        with st.form("create_case"):
            col1, col2 = st.columns(2)
            client_name = col1.text_input("Client name", "New Client")
            organization = col2.text_input("Organization")
            contact_person = col1.text_input("Contact person")
            email = col2.text_input("Email")
            whatsapp = col1.text_input("WhatsApp")
            tender_title = col2.text_input("Tender title", "Untitled donor tender")
            donor_client = col1.text_input("Donor/client")
            country = col2.text_input("Country")
            sector = col1.text_input("Sector")
            submission_deadline = col2.text_input("Submission deadline", placeholder="YYYY-MM-DD")
            submission_type = col1.text_input("Submission type", "Technical + Financial")
            bidding_role = col2.text_input("Bidding role", "Lead bidder")
            diagnostic_type = col1.text_input("Diagnostic type", "TenderProof Rapid Bid Diagnostic")
            payment_status = col2.text_input("Payment status", "unpaid")
            if st.form_submit_button("Create diagnostic case", type="primary"):
                case = create_case(
                    session,
                    client_name=client_name,
                    organization=organization,
                    contact_person=contact_person,
                    email=email,
                    whatsapp=whatsapp,
                    tender_title=tender_title,
                    donor_client=donor_client,
                    country=country,
                    sector=sector,
                    submission_deadline=submission_deadline,
                    submission_type=submission_type,
                    bidding_role=bidding_role,
                    diagnostic_type=diagnostic_type,
                    payment_status=payment_status,
                )
                set_active_case(case.case_id)
                session.commit()
                st.success(f"Created and opened {case.case_id}")
                st.rerun()
    with tab_open:
        case = case_selector(session)
        if case:
            with st.form("update_case"):
                col1, col2 = st.columns(2)
                client_name = col1.text_input("Client name", case.client_name or "")
                tender_title = col2.text_input("Tender title", case.tender_title or "")
                donor_client = col1.text_input("Donor/client", case.donor_client or "")
                country = col2.text_input("Country", case.country or "")
                sector = col1.text_input("Sector", case.sector or "")
                deadline = col2.text_input("Submission deadline", case.submission_deadline or "")
                editable_statuses = [value for value in CASE_STATUSES if value not in {"client_ready", "packaged"}]
                status = col1.selectbox("Status", editable_statuses, index=editable_statuses.index(case.status) if case.status in editable_statuses else 0)
                payment = col2.text_input("Payment status", case.payment_status or "")
                if st.form_submit_button("Save case changes"):
                    update_case(session, case.case_id, client_name=client_name, tender_title=tender_title, donor_client=donor_client, country=country, sector=sector, submission_deadline=deadline, status=status, payment_status=payment)
                    session.commit()
                    st.success("Case updated.")
                    st.rerun()
