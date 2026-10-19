import json
from uuid import uuid4

from sqlalchemy.orm import Session

from ..models import AuditEvent


def log_event(session: Session, case_id: str | None, event_type: str, message: str, payload: dict | None = None) -> AuditEvent:
    event = AuditEvent(
        event_id=f"AUD-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        event_type=event_type,
        event_message=message,
        event_payload_json=json.dumps(payload or {}, default=str),
    )
    session.add(event)
    session.flush()
    return event


def latest_events(session: Session, limit: int = 20, case_id: str | None = None) -> list[AuditEvent]:
    query = session.query(AuditEvent)
    if case_id:
        query = query.filter(AuditEvent.case_id == case_id)
    return query.order_by(AuditEvent.created_at.desc()).limit(limit).all()

