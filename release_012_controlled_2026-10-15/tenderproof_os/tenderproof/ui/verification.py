import streamlit as st

from ..models import AuditEvent, ComplianceLedger, DecisionApproval, EvidenceReview, VerificationResult, VerificationRun
from ..services.approval_service import approve_case, record_evidence_review, review_source, revoke_approval
from ..services.decision_service import active_sources, release_context
from ..services.verification_service import run_verification
from .helpers import require_case, show_table


def render(session) -> None:
    st.title("Verification / Audit Log")
    case = require_case(session)
    if not case:
        return
    context = release_context(session, case.case_id)
    a, b, c = st.columns(3)
    a.metric("Eligibility", context["eligibility"])
    b.metric("Release", context["readiness_label"])
    c.metric("Approval", "Current" if context["approved"] else "Pending / stale")
    st.caption(f"Assessment {context['snapshot_hash'][:16]}")
    checks, sources, evidence, approvals, history = st.tabs(["Current checks", "Source reviews", "Evidence reviews", "Human approval", "History"])
    with checks:
        if st.button("Run verification", type="primary"):
            run_verification(session, case.case_id)
            session.commit()
            st.rerun()
        latest = session.query(VerificationRun).filter_by(case_id=case.case_id).order_by(VerificationRun.id.desc()).first()
        if latest:
            if latest.snapshot_hash != context["snapshot_hash"]:
                st.warning("Verification is stale.")
            show_table(session.query(VerificationResult).filter_by(case_id=case.case_id, run_id=latest.run_id).order_by(VerificationResult.id).all())
        else:
            st.info("Verification pending.")
    with sources:
        source_items = active_sources(session, case.case_id)
        show_table(source_items, "No source registered.")
        if source_items:
            with st.form("source_review"):
                source_id = st.selectbox("Source version", [s.source_id for s in source_items], format_func=lambda sid: next(f"{s.filename} / v{s.version_number}" for s in source_items if s.source_id == sid))
                reviewer = st.text_input("Source reviewer")
                notes = st.text_area("Source review rationale")
                complete = st.checkbox("All applicable clauses captured and reviewed")
                if st.form_submit_button("Record source review"):
                    try:
                        review_source(session, case.case_id, source_id, reviewer=reviewer, notes=notes, requirements_complete=complete)
                        session.commit()
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
    with evidence:
        rows = session.query(ComplianceLedger).filter_by(case_id=case.case_id).all()
        source_rows = active_sources(session, case.case_id)
        if rows and source_rows:
            with st.form("evidence_review"):
                compliance_id = st.selectbox("Compliance evidence", [r.compliance_id for r in rows], format_func=lambda cid: next(f"{r.requirement_id} / {r.status}" for r in rows if r.compliance_id == cid))
                source_id = st.selectbox("Supporting source", [s.source_id for s in source_rows], format_func=lambda sid: next(f"{s.filename} / v{s.version_number}" for s in source_rows if s.source_id == sid))
                legal_entity = st.text_input("Evidence legal entity", case.organization or case.client_name or "")
                reviewer = st.text_input("Evidence reviewer")
                status = st.selectbox("Evidence review result", ["pending", "verified", "failed", "not_applicable"])
                c1, c2 = st.columns(2)
                valid_from = c1.date_input("Valid from", value=None)
                valid_until = c2.date_input("Valid until", value=None)
                validity_reason = st.text_input("Reason expiry does not apply")
                notes = st.text_area("Evidence review rationale")
                if st.form_submit_button("Record evidence review"):
                    try:
                        record_evidence_review(session, case.case_id, compliance_id, reviewer=reviewer, notes=notes, legal_entity=legal_entity, source_id=source_id, valid_from=valid_from.isoformat() if valid_from else None, valid_until=valid_until.isoformat() if valid_until else None, validity_reason=validity_reason, review_status=status)
                        session.commit()
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
        show_table(session.query(EvidenceReview).filter_by(case_id=case.case_id).order_by(EvidenceReview.id.desc()).all(), "No evidence reviews.")
    with approvals:
        with st.form("human_approval"):
            reviewer = st.text_input("Approver name")
            rationale = st.text_area("Approval rationale")
            confirmed = st.checkbox("I approve the current evidence snapshot")
            if st.form_submit_button("Approve current assessment", type="primary"):
                try:
                    if not confirmed:
                        raise ValueError("Confirm the current assessment before approving.")
                    approve_case(session, case.case_id, reviewer=reviewer, rationale=rationale)
                    session.commit()
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        approvals_rows = session.query(DecisionApproval).filter_by(case_id=case.case_id).order_by(DecisionApproval.id.desc()).all()
        show_table(approvals_rows, "No recorded approvals.")
        active = [a for a in approvals_rows if a.revoked_at is None]
        if active:
            with st.expander("Revoke approval"):
                with st.form("revoke_approval"):
                    selected = st.selectbox("Approval", [a.approval_id for a in active])
                    who = st.text_input("Revoking reviewer")
                    reason = st.text_area("Revocation reason")
                    if st.form_submit_button("Revoke selected approval"):
                        try:
                            revoke_approval(session, case.case_id, selected, reviewer=who, reason=reason)
                            session.commit()
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))
    with history:
        st.subheader("Verification history")
        show_table(session.query(VerificationRun).filter_by(case_id=case.case_id).order_by(VerificationRun.id.desc()).all(), "No historical runs.")
        st.subheader("Audit events")
        show_table(session.query(AuditEvent).filter_by(case_id=case.case_id).order_by(AuditEvent.created_at.desc()).limit(100).all(), "No audit events.")

