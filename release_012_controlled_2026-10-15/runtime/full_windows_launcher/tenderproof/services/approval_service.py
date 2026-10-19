"""Attributable local reviews and approvals tied to exact input snapshots."""

from datetime import UTC, date, datetime
from uuid import uuid4
from pathlib import Path
import shutil

from ..models import Case, ComplianceLedger, DecisionApproval, EvidenceReview, NormalizedRequirement, Source
from ..config import EVIDENCE_DIR, ensure_directories
from .audit_service import log_event
from .decision_service import (
    active_sources, current_approval, evidence_problem, file_hash, invalidate_case,
    latest_current_run, policy_assessment, release_context, snapshot_hash,
    source_review_problem, text_hash, today,
)


def _attribution(reviewer, notes):
    if not reviewer or not reviewer.strip() or not notes or not notes.strip():
        raise ValueError("A named reviewer and review rationale are required.")


def review_source(session, case_id, source_id, *, reviewer, notes, requirements_complete=False):
    _attribution(reviewer, notes)
    source = session.query(Source).filter_by(case_id=case_id, source_id=source_id).first()
    if source is None or source not in active_sources(session, case_id):
        raise ValueError("Select a current source belonging to this case.")
    issue = source_review_problem(source)
    if issue and issue[0] == "blocker":
        raise ValueError(issue[1])
    if not requirements_complete:
        raise ValueError("Confirm that all applicable source requirements have been captured and reviewed.")
    source.content_sha256 = file_hash(source.file_path) if source.file_path else file_hash(source.text_extract_path)
    source.text_sha256 = file_hash(source.text_extract_path)
    source.reviewed_sha256, source.reviewed_text_sha256 = source.content_sha256, source.text_sha256
    source.reviewed_by, source.review_notes = reviewer.strip(), notes.strip()
    source.reviewed_at = datetime.now(UTC)
    source.requirements_complete = True
    invalidate_case(session, case_id, f"Source review recorded for {source_id}.")
    return source


def record_evidence_review(session, case_id, compliance_id, *, reviewer, notes, legal_entity, source_id=None, file_path=None, valid_from=None, valid_until=None, validity_reason="", review_status="verified"):
    _attribution(reviewer, notes)
    case = session.query(Case).filter_by(case_id=case_id).first()
    row = session.query(ComplianceLedger).filter_by(case_id=case_id, compliance_id=compliance_id).first()
    if case is None or row is None:
        raise ValueError("Evidence and case must exist and belong together.")
    req = session.query(NormalizedRequirement).filter_by(case_id=case_id, requirement_id=row.requirement_id).first()
    if req is None or req.needs_review:
        raise ValueError("Review the associated requirement first.")
    if review_status not in {"verified", "failed", "pending", "not_applicable"}:
        raise ValueError("Unknown evidence review state.")
    if review_status in {"verified", "not_applicable"} and (legal_entity or "").strip().casefold() != (case.organization or case.client_name or "").strip().casefold():
        raise ValueError("Evidence legal entity must match this bidder.")
    if not source_id and not file_path:
        raise ValueError("Link an actual reviewed source or evidence attachment.")
    if source_id:
        source = next((s for s in active_sources(session, case_id) if s.source_id == source_id), None)
        if source is None or source_review_problem(source):
            raise ValueError("The linked evidence source needs a current review.")
    file_digest = file_hash(file_path)
    if file_path and not file_digest:
        raise ValueError("Evidence attachment does not exist.")
    start = date.fromisoformat(valid_from) if valid_from else None
    end = date.fromisoformat(valid_until) if valid_until else None
    if start and end and start > end:
        raise ValueError("Evidence validity start is after its end.")
    if review_status == "not_applicable" and row.status != "Not Applicable":
        raise ValueError("An exclusion review requires a Not Applicable compliance row and source-based rationale.")
    if review_status == "verified" and not end and not validity_reason.strip():
        raise ValueError("Specify an expiry date or a reviewed reason why expiry does not apply.")
    if review_status == "verified":
        if row.status != "Met" or evidence_problem(row.available_evidence):
            raise ValueError("Only resolved evidence on a Met row can be verified.")
        current_date = today()
        if (start and start > current_date) or (end and end < current_date):
            raise ValueError("Evidence is expired or not yet valid.")
    evidence_id = f"EVD-{uuid4().hex[:12].upper()}"
    archived = None
    if file_path:
        ensure_directories()
        archived = EVIDENCE_DIR / f"{evidence_id}{Path(file_path).suffix.lower()}"
        shutil.copyfile(file_path, archived)
        if file_hash(archived) != file_digest or file_hash(file_path) != file_digest:
            raise ValueError("Evidence changed during archival; review the attachment again.")
    review = EvidenceReview(
        evidence_id=evidence_id, case_id=case_id,
        requirement_id=req.requirement_id, compliance_id=compliance_id,
        evidence_text_sha256=text_hash(row.available_evidence), source_id=source_id,
        file_path=str(file_path) if file_path else None, file_sha256=file_digest,
        archive_file_path=str(archived) if archived else None, archive_sha256=file_digest,
        legal_entity=legal_entity.strip(), valid_from=valid_from, valid_until=valid_until,
        validity_reason=validity_reason.strip(), review_status=review_status,
        reviewed_by=reviewer.strip(), review_notes=notes.strip(),
    )
    session.add(review)
    invalidate_case(session, case_id, f"Evidence review recorded for {compliance_id}.")
    return review


def approve_case(session, case_id, *, reviewer, rationale):
    _attribution(reviewer, rationale)
    policy = policy_assessment(session, case_id)
    fingerprint = snapshot_hash(session, case_id)
    run = latest_current_run(session, case_id, fingerprint)
    if policy["eligibility"] not in {"PASS", "NOT_APPLICABLE"} or policy["blockers"] or policy["warnings"] or run is None or not run.technical_passed:
        raise ValueError("Approval requires current, fully reviewed evidence and a successful verification run.")
    existing = current_approval(session, case_id, fingerprint)
    if existing:
        return existing
    approval = DecisionApproval(approval_id=f"APP-{uuid4().hex[:12].upper()}", case_id=case_id, snapshot_hash=fingerprint, verification_run_id=run.run_id, approved_by=reviewer.strip(), rationale=rationale.strip())
    session.add(approval)
    session.flush()
    context = release_context(session, case_id)
    case = session.query(Case).filter_by(case_id=case_id).one()
    case.readiness_label = context["readiness_label"]
    log_event(session, case_id, "decision.approved", f"Snapshot approved by {reviewer.strip()}.", {"approval_id": approval.approval_id, "snapshot_hash": fingerprint})
    return approval


def revoke_approval(session, case_id, approval_id, *, reviewer, reason):
    _attribution(reviewer, reason)
    approval = session.query(DecisionApproval).filter_by(case_id=case_id, approval_id=approval_id).one()
    approval.revoked_at = datetime.now(UTC)
    approval.revocation_reason = f"{reviewer.strip()}: {reason.strip()}"
    invalidate_case(session, case_id, f"Approval {approval_id} revoked: {reason.strip()}")
