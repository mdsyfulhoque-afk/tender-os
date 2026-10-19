from pathlib import Path
from uuid import uuid4

import pandas as pd
from sqlalchemy.orm import Session

from ..config import EXPORTS_DIR, ensure_directories
from ..models import IPCapture
from .audit_service import log_event


def add_ip_capture(session: Session, case_id: str, **data) -> IPCapture:
    row = IPCapture(
        ip_id=f"IP-{uuid4().hex[:10].upper()}",
        case_id=case_id,
        donor=data.get("donor") or "",
        sector=data.get("sector") or "",
        country=data.get("country") or "",
        pattern_type=data.get("pattern_type") or "ToR pattern",
        pattern_title=data.get("pattern_title") or "",
        pattern_description=data.get("pattern_description") or "",
        reusable_asset=data.get("reusable_asset") or "",
        anonymized=bool(data.get("anonymized", True)),
        confidence_level=data.get("confidence_level") or "medium",
        notes=data.get("notes") or "",
    )
    session.add(row)
    session.flush()
    log_event(session, case_id, "ip_capture.created", f"Captured reusable IP pattern {row.ip_id}")
    return row


def list_ip(session: Session, case_id: str) -> list[IPCapture]:
    return session.query(IPCapture).filter(IPCapture.case_id == case_id).order_by(IPCapture.created_at.desc()).all()


def export_ip_csv(session: Session, case_id: str) -> Path:
    ensure_directories()
    rows = []
    for row in list_ip(session, case_id):
        values = {c.name: getattr(row, c.name) for c in row.__table__.columns}
        for key, value in values.items():
            if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                values[key] = "'" + value
        rows.append(values)
    path = EXPORTS_DIR / f"{case_id}_ip_capture.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    log_event(session, case_id, "ip_capture.export", f"Exported IP capture CSV {path.name}")
    return path

