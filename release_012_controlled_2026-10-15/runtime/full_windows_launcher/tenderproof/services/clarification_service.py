import re
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import ClarificationQuestion


def _logical_text(value: str | None) -> str:
    return re.sub(r"\W+", " ", (value or "").casefold()).strip()


def add_clarification_question(
    session: Session,
    case_id: str,
    *,
    question: str,
    related_requirement_id: str | None = None,
    why_it_matters: str = "",
    priority: str = "medium",
    status: str = "open",
) -> ClarificationQuestion:
    normalized = _logical_text(question)
    existing = session.query(ClarificationQuestion).filter_by(case_id=case_id).all()
    for row in existing:
        if _logical_text(row.question) == normalized:
            return row

    row = ClarificationQuestion(
        question_id=f"Q-{uuid4().hex[:12].upper()}",
        case_id=case_id,
        related_requirement_id=related_requirement_id,
        question=question.strip(),
        why_it_matters=why_it_matters,
        priority=priority,
        status=status,
    )
    try:
        with session.begin_nested():
            session.add(row)
            session.flush()
        return row
    except IntegrityError:
        # Preserve the caller's transaction and return the competing logical row.
        for existing in session.query(ClarificationQuestion).filter_by(case_id=case_id).all():
            if _logical_text(existing.question) == normalized:
                return existing
        raise
