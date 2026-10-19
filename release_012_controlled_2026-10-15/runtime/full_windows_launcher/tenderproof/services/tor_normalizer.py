import hashlib
import re
from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import GapItem, NormalizedRequirement


def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = re.sub(r"\s+([,.;:)])", r"\1", normalized)
    normalized = re.sub(r"([(])\s+", r"\1", normalized)
    return normalized.strip()


def _hashable(text: str) -> str:
    text = normalize_text(text).lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_atomic_requirements(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    lines = []
    for raw in normalized.split("\n"):
        raw = raw.strip(" -\t")
        if not raw:
            continue
        segments = re.split(
            r"(?<=[.;])\s+(?=(?:The |Consultant|Bidder|Expert|Team|Proposal|CV|Methodology|Must|Shall|Provide|Include|Submit))",
            raw,
        )
        for segment in segments:
            segment = segment.strip(" -")
            if len(segment) >= 18:
                lines.append(segment)
    if not lines and len(normalized) >= 18:
        lines.append(normalized)
    return lines


def generate_match_key(case_id: str, category: str, section_ref: str, requirement_text: str) -> str:
    material = "|".join(
        [
            _hashable(case_id),
            _hashable(category or "uncategorized"),
            _hashable(section_ref or "unknown-section"),
            _hashable(requirement_text),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def generate_canonical_anchor(source_id: str, section_ref: str, row_number: int) -> str:
    source = source_id or "MANUAL"
    section = re.sub(r"\s+", "-", (section_ref or "unknown-section").strip().lower())
    return f"{source}:{section}:REQ-{row_number:04d}"


def detect_duplicate_match_key(session: Session, case_id: str, match_key: str) -> bool:
    return (
        session.query(NormalizedRequirement)
        .filter(NormalizedRequirement.case_id == case_id, NormalizedRequirement.match_key == match_key)
        .first()
        is not None
    )


def create_requirement_rows(case_id: str, source_id: str, extracted_text: str) -> list[dict]:
    normalized = normalize_text(extracted_text)
    atomic_items = split_atomic_requirements(normalized)
    rows: list[dict] = []
    for idx, item in enumerate(atomic_items, start=1):
        section_ref = f"auto-{idx}"
        lower = item.lower()
        mandatory = any(marker in lower for marker in ["shall", "must", "required", "mandatory", "submit", "provide"])
        category = _guess_category(item)
        rows.append(
            {
                "requirement_id": f"REQ-{uuid4().hex[:10].upper()}",
                "case_id": case_id,
                "source_id": source_id,
                "tor_section_page": section_ref,
                "requirement_category": category,
                "requirement_text": item,
                "atomic_requirement_text": item,
                "mandatory": mandatory,
                "interpretation": "",
                "evidence_needed": _guess_evidence_needed(item),
                "proposal_section_affected": _guess_proposal_section(item),
                "expert_role_affected": "",
                "deliverable_affected": "",
                "evaluation_weight": "",
                "form_annex_required": "",
                "clarification_needed": False,
                "risk_level": "medium",
                "match_key": generate_match_key(case_id, category, section_ref, item),
                "canonical_anchor": generate_canonical_anchor(source_id, section_ref, idx),
                "needs_review": True,
                "notes": "Auto-normalized. Human review required before client-ready use.",
            }
        )
    return rows


def create_gap_for_failed_extraction(session: Session, case_id: str, source_id: str, reason: str) -> GapItem:
    gap = GapItem(
        gap_id=f"GAP-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        related_requirement_id=None,
        related_compliance_id=None,
        related_cv_match_id=None,
        gap_type="source extraction",
        gap_description=f"Text extraction failed for source {source_id}: {reason}",
        required_action="Manually paste ToR text or re-upload a readable PDF/DOCX/TXT.",
        status="open",
    )
    session.add(gap)
    session.flush()
    return gap


def _guess_category(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ["expert", "key personnel", "cv", "qualification"]):
        return "cv/expert"
    if any(word in lower for word in ["methodology", "approach", "work plan"]):
        return "methodology"
    if any(word in lower for word in ["annex", "form", "submission", "deadline"]):
        return "submission/compliance"
    if any(word in lower for word in ["deliverable", "report", "output"]):
        return "deliverable"
    return "technical requirement"


def _guess_evidence_needed(text: str) -> str:
    lower = text.lower()
    if "cv" in lower or "expert" in lower:
        return "CV evidence, role mapping, years and donor/country experience proof."
    if "methodology" in lower:
        return "Methodology section showing approach, workplan, staffing, and quality assurance."
    if "annex" in lower or "form" in lower:
        return "Completed annex/form and submission checklist evidence."
    return "Proposal text, supporting document, or client input proving compliance."


def _guess_proposal_section(text: str) -> str:
    lower = text.lower()
    if "cv" in lower or "expert" in lower:
        return "Key Experts / Team Composition"
    if "methodology" in lower or "approach" in lower:
        return "Technical Approach and Methodology"
    if "deliverable" in lower:
        return "Workplan and Deliverables"
    return "Compliance Matrix / Technical Proposal"

