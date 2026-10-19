from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import ComplianceLedger, CVMatch, GapItem, NormalizedRequirement
from .audit_service import log_event


def create_gap(
    session: Session,
    case_id: str,
    gap_type: str,
    gap_description: str,
    required_action: str,
    related_requirement_id: str | None = None,
    related_compliance_id: str | None = None,
    related_cv_match_id: str | None = None,
    owner: str | None = "",
    due_date: str | None = "",
) -> GapItem:
    existing = session.query(GapItem).filter(
        GapItem.case_id == case_id,
        GapItem.related_requirement_id == related_requirement_id,
        GapItem.related_compliance_id == related_compliance_id,
        GapItem.related_cv_match_id == related_cv_match_id,
        GapItem.gap_type == gap_type,
    ).first()
    if existing:
        return existing
    gap = GapItem(
        gap_id=f"GAP-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        related_requirement_id=related_requirement_id,
        related_compliance_id=related_compliance_id,
        related_cv_match_id=related_cv_match_id,
        gap_type=gap_type,
        gap_description=gap_description,
        required_action=required_action,
        owner=owner or "",
        due_date=due_date or "",
        status="open",
    )
    session.add(gap)
    session.flush()
    log_event(session, case_id, "gap.created", f"Created gap {gap.gap_id}: {gap_type}")
    return gap


def sync_gaps_from_compliance(session: Session, case_id: str) -> list[GapItem]:
    created = []
    rows = session.query(ComplianceLedger).filter(ComplianceLedger.case_id == case_id).all()
    reqs = {r.requirement_id: r for r in session.query(NormalizedRequirement).filter(NormalizedRequirement.case_id == case_id).all()}
    for row in rows:
        evidence = (row.available_evidence or "").strip()
        should_gap = row.status in {"Gap", "Pending Input"} or (reqs.get(row.requirement_id) and reqs[row.requirement_id].mandatory and not evidence)
        if should_gap:
            gap = create_gap(
                session,
                case_id=case_id,
                gap_type="compliance",
                gap_description=row.gap or f"Missing or incomplete evidence for {row.requirement_id}",
                required_action=row.action_required or "Collect evidence or mark requirement as not applicable with rationale.",
                related_requirement_id=row.requirement_id,
                related_compliance_id=row.compliance_id,
            )
            created.append(gap)
    return created


def sync_gaps_from_cv(session: Session, case_id: str) -> list[GapItem]:
    created = []
    rows = session.query(CVMatch).filter(CVMatch.case_id == case_id).all()
    for row in rows:
        if row.gap or row.replace_candidate or (row.match_score_1_to_5 is not None and row.match_score_1_to_5 <= 2):
            gap = create_gap(
                session,
                case_id=case_id,
                gap_type="cv/expert",
                gap_description=row.gap or f"Low CV match for {row.candidate_name or 'candidate'} as {row.expert_role or 'expert'}",
                required_action="Improve CV evidence, rewrite role-specific CV language, or replace candidate.",
                related_requirement_id=row.requirement_id,
                related_cv_match_id=row.expert_match_id,
            )
            created.append(gap)
    return created


def list_gaps(session: Session, case_id: str) -> list[GapItem]:
    return session.query(GapItem).filter(GapItem.case_id == case_id).order_by(GapItem.created_at.desc()).all()

