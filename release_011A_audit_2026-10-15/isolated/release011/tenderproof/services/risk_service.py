from uuid import uuid4
import re

from sqlalchemy.orm import Session

from ..models import GapItem, RiskRegister
from .audit_service import log_event


def add_risk(session: Session, case_id: str, **data) -> RiskRegister:
    risk = RiskRegister(
        risk_id=f"RISK-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        risk_category=data.get("risk_category") or "delivery",
        risk_description=data.get("risk_description") or "",
        source_requirement_id=data.get("source_requirement_id") or "",
        severity=data.get("severity") or "medium",
        likelihood=data.get("likelihood") or "medium",
        mitigation=data.get("mitigation") or "",
        owner=data.get("owner") or "",
        due_date=data.get("due_date") or "",
        status=data.get("status") or "open",
    )
    session.add(risk)
    session.flush()
    log_event(session, case_id, "risk.created", f"Created risk {risk.risk_id}")
    return risk


def auto_generate_risks_from_gaps(session: Session, case_id: str) -> list[RiskRegister]:
    created = []
    gaps = session.query(GapItem).filter(GapItem.case_id == case_id).all()
    def risk_key(requirement_id: str | None, description: str | None) -> tuple[str, str]:
        normalized_description = re.sub(r"\W+", " ", (description or "").casefold()).strip()
        return requirement_id or "", normalized_description

    existing_keys = {
        risk_key(risk.source_requirement_id, risk.risk_description)
        for risk in session.query(RiskRegister).filter(RiskRegister.case_id == case_id).all()
    }
    for gap in gaps:
        desc = f"Open gap may weaken proposal: {gap.gap_description}"
        key = risk_key(gap.related_requirement_id, desc)
        if key in existing_keys:
            continue
        risk = add_risk(
            session,
            case_id,
            risk_category=gap.gap_type or "gap",
            risk_description=desc,
            source_requirement_id=gap.related_requirement_id or "",
            severity="high" if (gap.gap_type or "").lower() in {"compliance", "cv/expert"} else "medium",
            likelihood="medium",
            mitigation=gap.required_action or "Resolve gap before client-ready package.",
        )
        created.append(risk)
        existing_keys.add(key)
    return created


def list_risks(session: Session, case_id: str) -> list[RiskRegister]:
    return session.query(RiskRegister).filter(RiskRegister.case_id == case_id).order_by(RiskRegister.created_at.desc()).all()

