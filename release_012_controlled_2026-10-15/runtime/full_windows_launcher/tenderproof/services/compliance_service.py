from uuid import uuid4

from sqlalchemy.orm import Session

from ..constants import COMPLIANCE_STATUSES
from ..models import ComplianceLedger, NormalizedRequirement
from .audit_service import log_event
from .gap_service import sync_gaps_from_compliance
from .decision_service import invalidate_case


def auto_create_compliance_rows(session: Session, case_id: str) -> list[ComplianceLedger]:
    created = []
    reqs = session.query(NormalizedRequirement).filter(NormalizedRequirement.case_id == case_id).all()
    existing_ids = {
        row.requirement_id
        for row in session.query(ComplianceLedger.requirement_id).filter(ComplianceLedger.case_id == case_id).all()
    }
    for req in reqs:
        if req.requirement_id in existing_ids:
            continue
        row = ComplianceLedger(
            compliance_id=f"COMP-{uuid4().hex[:10].upper()}",
            requirement_id=req.requirement_id,
            case_id=case_id,
            evidence_needed=req.evidence_needed or "",
            available_evidence="",
            gap="Missing evidence." if req.mandatory else "",
            proposal_location=req.proposal_section_affected or "",
            responsible_person="",
            status="Pending Input" if req.mandatory else "Not Applicable",
            risk_level=req.risk_level or "medium",
            action_required="Collect evidence and confirm proposal location." if req.mandatory else "",
            deadline="",
            final_check="",
            notes="Auto-created from normalized requirement.",
        )
        session.add(row)
        created.append(row)
    session.flush()
    sync_gaps_from_compliance(session, case_id)
    if created:
        invalidate_case(session, case_id, "Compliance requirements added.")
    log_event(session, case_id, "compliance.sync", f"Auto-created {len(created)} compliance rows")
    return created


def update_compliance_row(session: Session, compliance_id: str, **data) -> ComplianceLedger | None:
    row = session.query(ComplianceLedger).filter(ComplianceLedger.compliance_id == compliance_id).first()
    if not row:
        return None
    fields = {
        "evidence_needed",
        "available_evidence",
        "gap",
        "proposal_location",
        "responsible_person",
        "status",
        "risk_level",
        "action_required",
        "deadline",
        "final_check",
        "notes",
    }
    for key, value in data.items():
        if key in fields and value is not None:
            if key == "status" and value not in COMPLIANCE_STATUSES:
                continue
            setattr(row, key, value)
    session.flush()
    sync_gaps_from_compliance(session, row.case_id)
    invalidate_case(session, row.case_id, f"Compliance or evidence changed: {compliance_id}")
    log_event(session, row.case_id, "compliance.updated", f"Updated compliance row {row.compliance_id}")
    return row


def list_compliance(session: Session, case_id: str) -> list[ComplianceLedger]:
    return session.query(ComplianceLedger).filter(ComplianceLedger.case_id == case_id).order_by(ComplianceLedger.id).all()

