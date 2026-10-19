from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import CVMatch
from .audit_service import log_event
from .gap_service import sync_gaps_from_cv


def safe_cv_suggestion(cv_evidence: str, expert_role: str, requirement: str = "") -> str:
    evidence = (cv_evidence or "").strip()
    if not evidence:
        return "Pending Input: no CV evidence was provided, so no CV rewrite language can be generated."
    role = expert_role or "the proposed expert"
    req = f" This supports the requirement: {requirement.strip()}" if requirement.strip() else ""
    return f"{role} has documented evidence of: {evidence}.{req} Human review required before use."


def add_cv_match(session: Session, case_id: str, **data) -> CVMatch:
    evidence = data.get("cv_evidence") or ""
    score = int(data.get("match_score_1_to_5") or 0)
    match = CVMatch(
        expert_match_id=f"CVM-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        requirement_id=data.get("requirement_id") or "",
        expert_role=data.get("expert_role") or "",
        candidate_name=data.get("candidate_name") or "",
        required_qualification=data.get("required_qualification") or "",
        required_years=data.get("required_years") or "",
        required_specific_experience=data.get("required_specific_experience") or "",
        required_country_region_experience=data.get("required_country_region_experience") or "",
        required_donor_experience=data.get("required_donor_experience") or "",
        required_language_tools=data.get("required_language_tools") or "",
        cv_evidence=evidence,
        match_score_1_to_5=score,
        gap=data.get("gap") or ("" if score >= 3 and evidence else "Missing or weak CV evidence."),
        rewrite_needed=bool(data.get("rewrite_needed", False)),
        suggested_cv_language=data.get("suggested_cv_language") or safe_cv_suggestion(evidence, data.get("expert_role") or ""),
        replace_candidate=bool(data.get("replace_candidate", False)),
        risk_level=data.get("risk_level") or ("high" if score <= 2 else "medium"),
        notes=data.get("notes") or "",
    )
    session.add(match)
    session.flush()
    sync_gaps_from_cv(session, case_id)
    log_event(session, case_id, "cv_match.created", f"Added CV match for {match.candidate_name or match.expert_role}")
    return match


def list_cv_matches(session: Session, case_id: str) -> list[CVMatch]:
    return session.query(CVMatch).filter(CVMatch.case_id == case_id).order_by(CVMatch.id).all()

