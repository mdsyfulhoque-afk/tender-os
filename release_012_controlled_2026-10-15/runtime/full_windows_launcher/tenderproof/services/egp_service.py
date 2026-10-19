from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import EGPChecklistItem
from .audit_service import log_event


EGP_CHECKS = [
    ("rules", "Applicable rule version and transition", "PPR 2025 took effect on 28 September 2025; BPPA has since published a 2026 PPA amendment and a Rule 154 clarification. Check the current legal text, portal transition notice, clarification circular, tender issue date, and tender-specific instruction before deciding which provisions apply."),
    ("registration", "Correct registration type", "Confirm the e-GP registration type matches the actual bidder: national or international firm, individual consultant, or government-owned enterprise."),
    ("registration", "Current organization documents", "For applicable national firms, check incorporation/registration, trade licence, valid TIN and VAT evidence against the live portal's current registration list."),
    ("registration", "Authorized administrator and identity", "Confirm the organization authorization and administrator identity requirements are current. Avoid storing identity-document numbers in TenderProof."),
    ("registration", "Registration fee and account status", "Confirm any applicable e-GP registration fee is paid and the bidder account is active; verify directly in the portal."),
    ("opportunity", "Tender ID and closing time", "Record the tender reference and the exact portal closing date/time in Bangladesh Standard Time."),
    ("opportunity", "Current tender document and e-STD", "Use the current tender document available for this tender on e-GP; record its version and download date."),
    ("opportunity", "Amendments and clarifications", "Review every portal amendment, pre-tender meeting record, and published clarification; treat amendments as part of the tender document."),
    ("preparation", "Eligibility and qualification evidence", "Map every eligibility, experience, personnel, financial, and technical criterion to dated, verifiable evidence."),
    ("preparation", "Forms and response completeness", "Complete the portal forms and required schedules; check every question, criterion, and attachment against the tender document."),
    ("preparation", "Common Document Library validity", "Confirm reused e-GP briefcase/library files are authentic, current, legible, and valid for this tender."),
    ("preparation", "Price schedule / BOQ reconciliation", "Reconcile all quantities, units, arithmetic, taxes, and totals with the official schedule and portal fields; follow this tender's submission structure."),
    ("preparation", "Tender security, if required", "Check whether this tender requires security and verify exact form, amount, validity, and bank workflow from the current tender document and portal. Do not assume a standard amount."),
    ("submission", "Authorized e-signature / digital signature", "Confirm the authorized representative and the signature method required by the current e-GP process for this submission."),
    ("submission", "Upload review and integrity", "Check file readability, correct tender/field placement, completeness, and final preview before signing and submission."),
    ("submission", "Portal submission and receipt", "Submit through e-GP well before the deadline and retain the portal-generated submission confirmation. Late submissions may be rejected."),
    ("post_award", "Notification of Award and acceptance", "If awarded, review the NOA response deadline and acceptance steps in the live portal and contract documents."),
    ("post_award", "Performance security and contract", "If required, arrange the specified performance security and complete contract execution according to the NOA and tender-specific terms."),
    ("post_award", "e-CMS delivery controls", "For contracts managed in e-CMS, track the approved work plan, milestones, progress evidence, variations, invoices, and completion records."),
]


def ensure_egp_checklist(session: Session, case_id: str) -> list[EGPChecklistItem]:
    from .decision_service import invalidate_case
    existing = {item.item_key for item in session.query(EGPChecklistItem).filter_by(case_id=case_id).all()}
    for item_key, (stage, title, guidance) in enumerate(EGP_CHECKS):
        key = f"egp-{item_key + 1:02d}"
        if key not in existing:
            session.add(EGPChecklistItem(
                checklist_id=f"EGP-{uuid4().hex[:10].upper()}",
                case_id=case_id,
                item_key=key,
                stage=stage,
                item_title=title,
                guidance=guidance,
                status="Pending Input",
            ))
    session.flush()
    if len(existing) < len(EGP_CHECKS):
        invalidate_case(session, case_id, "Bangladesh e-GP assessment checklist activated.")
    return list_egp_checklist(session, case_id)


def list_egp_checklist(session: Session, case_id: str) -> list[EGPChecklistItem]:
    return (
        session.query(EGPChecklistItem)
        .filter_by(case_id=case_id)
        .order_by(EGPChecklistItem.id)
        .all()
    )


def update_egp_checklist(session: Session, case_id: str, updates: list[dict]) -> None:
    from .decision_service import invalidate_case
    items = {item.item_key: item for item in list_egp_checklist(session, case_id)}
    changed = 0
    for update in updates:
        item = items.get(update.get("item_key"))
        if not item:
            continue
        status = update.get("status")
        if status in {"Met", "Pending Input", "Gap", "Not Applicable"}:
            item.status = status
        item.evidence_notes = (update.get("evidence_notes") or "").strip()
        changed += 1
    session.flush()
    if changed:
        invalidate_case(session, case_id, "Bangladesh e-GP checklist changed.")
    log_event(session, case_id, "egp.checklist.updated", f"Updated {changed} Bangladesh e-GP readiness checks")
