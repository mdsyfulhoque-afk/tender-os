from uuid import uuid4

from sqlalchemy.orm import Session

from ..constants import CASE_STATUSES, READINESS_LABELS
from ..models import Case
from .audit_service import log_event
from .decision_service import invalidate_case


def make_case_id() -> str:
    return f"TP-{uuid4().hex[:8].upper()}"


def create_case(session: Session, **data) -> Case:
    case = Case(
        case_id=data.get("case_id") or make_case_id(),
        client_name=data.get("client_name") or "New Client",
        organization=data.get("organization") or "",
        contact_person=data.get("contact_person") or "",
        email=data.get("email") or "",
        whatsapp=data.get("whatsapp") or "",
        tender_title=data.get("tender_title") or "Untitled donor tender",
        donor_client=data.get("donor_client") or "",
        country=data.get("country") or "",
        sector=data.get("sector") or "",
        submission_deadline=data.get("submission_deadline") or "",
        submission_type=data.get("submission_type") or "",
        bidding_role=data.get("bidding_role") or "",
        diagnostic_type=data.get("diagnostic_type") or "Rapid Bid Diagnostic",
        status="draft",
        payment_status=data.get("payment_status") or "unpaid",
        readiness_label="DRAFT_ONLY",
    )
    session.add(case)
    session.flush()
    log_event(session, case.case_id, "case.created", f"Created case {case.case_id}")
    return case


def list_cases(session: Session) -> list[Case]:
    return session.query(Case).order_by(Case.updated_at.desc()).all()


def get_case(session: Session, case_id: str | None) -> Case | None:
    if not case_id:
        return None
    return session.query(Case).filter(Case.case_id == case_id).first()


def update_case(session: Session, case_id: str, **data) -> Case | None:
    case = get_case(session, case_id)
    if not case:
        return None
    allowed = {
        "client_name",
        "organization",
        "contact_person",
        "email",
        "whatsapp",
        "tender_title",
        "donor_client",
        "country",
        "sector",
        "submission_deadline",
        "submission_type",
        "bidding_role",
        "diagnostic_type",
        "status",
        "payment_status",
        "readiness_label",
    }
    for key, value in data.items():
        if key in allowed and value is not None and key != "readiness_label" and not (key == "status" and value in {"client_ready", "packaged"}):
            setattr(case, key, value)
    invalidate_case(session, case_id, "Case details or requested state changed.")
    if data.get("status") in set(CASE_STATUSES) - {"client_ready", "packaged"}:
        case.status = data["status"]
    log_event(session, case.case_id, "case.updated", f"Updated case {case.case_id}")
    session.flush()
    return case

