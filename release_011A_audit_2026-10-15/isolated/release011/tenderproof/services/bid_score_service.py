from sqlalchemy.orm import Session

from ..constants import REQUIRED_BID_CATEGORIES
from ..models import (BidRecommendation, BidScorecard, NormalizedRequirement, ComplianceLedger)
from .audit_service import log_event


def ensure_scorecard_categories(session: Session, case_id: str) -> list[BidScorecard]:
    existing = {row.category: row for row in session.query(BidScorecard).filter(BidScorecard.case_id == case_id).all()}
    created = []
    for category in REQUIRED_BID_CATEGORIES:
        if category not in existing:
            row = BidScorecard(case_id=case_id, category=category, score=0, max_score=5, rationale="", evidence_or_gap_reference="")
            session.add(row)
            created.append(row)
    session.flush()
    if created:
        log_event(session, case_id, "bid_scorecard.initialized", f"Initialized {len(created)} score categories")
    return session.query(BidScorecard).filter(BidScorecard.case_id == case_id).order_by(BidScorecard.id).all()


def calculate_score(rows: list[BidScorecard]) -> tuple[int, int, float]:
    total = sum(max(0, min(int(row.score or 0), int(row.max_score or 5))) for row in rows)
    max_score = sum(int(row.max_score or 5) for row in rows)
    percentage = round((total / max_score) * 100, 2) if max_score else 0.0
    return total, max_score, percentage


def recommendation_for_percentage(percentage: float, missing_inputs: bool = False) -> str:
    if missing_inputs:
        return "Pending input"
    if percentage >= 80:
        return "Pursue"
    if percentage >= 65:
        return "Pursue with partner"
    if percentage >= 50:
        return "Pursue only as sub-consultant"
    return "Reject / No-bid"


def save_scores_and_recommendation(session: Session, case_id: str, scores: dict[str, dict]) -> BidRecommendation:
    rows = ensure_scorecard_categories(session, case_id)
    by_category = {row.category: row for row in rows}
    for category, payload in scores.items():
        row = by_category.get(category)
        if not row:
            continue
        row.score = int(payload.get("score", row.score or 0))
        row.rationale = payload.get("rationale", row.rationale or "")
        row.evidence_or_gap_reference = payload.get("evidence_or_gap_reference", row.evidence_or_gap_reference or "")
    session.flush()
    rows = session.query(BidScorecard).filter(BidScorecard.case_id == case_id).all()
    total, max_score, percentage = calculate_score(rows)
    missing_inputs = any((row.score or 0) <= 0 for row in rows)
    rec_text = recommendation_for_percentage(percentage, missing_inputs)

    requirements = session.query(NormalizedRequirement).filter_by(
        case_id=case_id, mandatory=True
    ).all()

    compliance = session.query(ComplianceLedger).filter_by(
        case_id=case_id
    ).all()

    by_requirement = {}
    for item in compliance:
        by_requirement.setdefault(item.requirement_id, []).append(item)

    unresolved = not requirements
    failed = False

    for requirement in requirements:
        rows_for_requirement = by_requirement.get(
            requirement.requirement_id, []
        )

        if requirement.needs_review or len(rows_for_requirement) != 1:
            unresolved = True
            continue

        row = rows_for_requirement[0]

        if row.status == "Gap":
            failed = True
        elif (
            row.status != "Met"
            or not (row.available_evidence or "").strip()
        ):
            unresolved = True

    if failed:
        rec_text = "Reject / No-bid"
    elif unresolved:
        rec_text = "Pending input"
    rec = session.query(BidRecommendation).filter(BidRecommendation.case_id == case_id).order_by(BidRecommendation.id.desc()).first()
    if not rec:
        rec = BidRecommendation(case_id=case_id)
        session.add(rec)
    rec.total_score = total
    rec.max_score = max_score
    rec.percentage = percentage
    rec.recommendation = rec_text
    rec.rationale = _rationale(rec_text, percentage)
    session.flush()
    log_event(session, case_id, "bid_recommendation.generated", f"Generated recommendation: {rec.recommendation} ({percentage}%)")
    return rec


def latest_recommendation(session: Session, case_id: str) -> BidRecommendation | None:
    return session.query(BidRecommendation).filter(BidRecommendation.case_id == case_id).order_by(BidRecommendation.updated_at.desc()).first()


def _rationale(rec: str, percentage: float) -> str:
    if rec == "Pending input":
        return "One or more bid/no-bid categories still need scoring before a reliable recommendation can be issued."
    return f"Recommendation based on weighted operating judgment score of {percentage}% across the required TenderProof categories."

