from sqlalchemy.orm import Session

from ..models import NormalizedRequirement, Source
from .audit_service import log_event
from .source_service import get_source_text
from .tor_normalizer import create_requirement_rows, detect_duplicate_match_key
from .decision_service import invalidate_case


def create_requirements_from_source(session: Session, case_id: str, source_id: str) -> list[NormalizedRequirement]:
    source = session.query(Source).filter(Source.case_id == case_id, Source.source_id == source_id).first()
    if not source:
        return []
    text = get_source_text(source)
    rows = create_requirement_rows(case_id, source_id, text)
    created = []
    for row in rows:
        if detect_duplicate_match_key(session, case_id, row["match_key"]):
            continue
        req = NormalizedRequirement(**row)
        session.add(req)
        created.append(req)
    session.flush()
    if created:
        invalidate_case(session, case_id, "Requirements extracted from source.")
    log_event(session, case_id, "requirements.extracted", f"Created {len(created)} requirement rows from {source_id}")
    return created


def add_manual_requirement(session: Session, case_id: str, **data) -> NormalizedRequirement:
    from .tor_normalizer import generate_canonical_anchor, generate_match_key, normalize_text
    from uuid import uuid4

    text = normalize_text(data.get("requirement_text") or data.get("atomic_requirement_text") or "")
    category = data.get("requirement_category") or "manual"
    section_ref = data.get("tor_section_page") or "manual"
    row_count = session.query(NormalizedRequirement).filter(NormalizedRequirement.case_id == case_id).count() + 1
    req = NormalizedRequirement(
        requirement_id=f"REQ-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        source_id=data.get("source_id") or "MANUAL",
        tor_section_page=section_ref,
        requirement_category=category,
        requirement_text=text,
        atomic_requirement_text=text,
        mandatory=bool(data.get("mandatory", True)),
        interpretation=data.get("interpretation") or "",
        evidence_needed=data.get("evidence_needed") or "",
        proposal_section_affected=data.get("proposal_section_affected") or "",
        expert_role_affected=data.get("expert_role_affected") or "",
        deliverable_affected=data.get("deliverable_affected") or "",
        evaluation_weight=data.get("evaluation_weight") or "",
        form_annex_required=data.get("form_annex_required") or "",
        clarification_needed=bool(data.get("clarification_needed", False)),
        risk_level=data.get("risk_level") or "medium",
        match_key=generate_match_key(case_id, category, section_ref, text),
        canonical_anchor=generate_canonical_anchor(data.get("source_id") or "MANUAL", section_ref, row_count),
        needs_review=bool(data.get("needs_review", True)),
        notes=data.get("notes") or "Manual requirement.",
    )
    session.add(req)
    session.flush()
    invalidate_case(session, case_id, "Manual requirement added.")
    log_event(session, case_id, "requirement.manual", f"Added manual requirement {req.requirement_id}")
    return req


def list_requirements(session: Session, case_id: str) -> list[NormalizedRequirement]:
    return session.query(NormalizedRequirement).filter(NormalizedRequirement.case_id == case_id).order_by(NormalizedRequirement.id).all()


def update_requirement(session: Session, requirement_id: str, **data) -> NormalizedRequirement | None:
    from .tor_normalizer import generate_match_key

    req = session.query(NormalizedRequirement).filter(NormalizedRequirement.requirement_id == requirement_id).first()
    if not req:
        return None
    fields = {
        "tor_section_page",
        "requirement_category",
        "requirement_text",
        "atomic_requirement_text",
        "mandatory",
        "interpretation",
        "evidence_needed",
        "proposal_section_affected",
        "expert_role_affected",
        "deliverable_affected",
        "evaluation_weight",
        "form_annex_required",
        "clarification_needed",
        "risk_level",
        "needs_review",
        "notes",
        "source_id",
    }
    for key, value in data.items():
        if key in fields and value is not None and key != "requirement_text":
            setattr(req, key, value)
    req.match_key = generate_match_key(req.case_id, req.requirement_category or "", req.tor_section_page or "", req.atomic_requirement_text or req.requirement_text)
    session.flush()
    invalidate_case(session, req.case_id, f"Requirement changed: {requirement_id}")
    log_event(session, req.case_id, "requirement.updated", f"Updated requirement {req.requirement_id}")
    return req
