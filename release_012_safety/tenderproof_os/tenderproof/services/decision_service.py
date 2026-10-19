"""Shared eligibility, input freshness and output release policy."""

from datetime import UTC, date, datetime
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from .. import models as m
from .audit_service import log_event

READY_LABELS = {"CLIENT_READY", "EXPORT_READY"}


def today():
    return datetime.now(ZoneInfo("Asia/Dhaka")).date()


def file_hash(value):
    if not value or not Path(value).is_file():
        return None
    digest = hashlib.sha256()
    try:
        with Path(value).open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def text_hash(value):
    return hashlib.sha256((value or "").strip().encode("utf-8")).hexdigest()


def evidence_problem(value):
    value = re.sub(r"\s+", " ", (value or "").strip()).casefold()
    if value in {"", "pending input", "pending", "unknown", "none", "n/a", "missing", "missing evidence", "not provided"}:
        return "Required evidence is missing or unresolved."
    if re.search(r"\bexpired on\b|\bbelongs to another\b|\bwrong legal entity\b", value):
        return "Evidence explicitly describes an invalid date or legal entity."
    return None


def invalidate_case(session, case_id, reason):
    case = session.query(m.Case).filter_by(case_id=case_id).first()
    if case is None:
        raise ValueError(f"Unknown case: {case_id}")
    case.assessment_revision = (case.assessment_revision or 0) + 1
    case.readiness_label, case.status = "DRAFT_ONLY", "draft"
    for output in session.query(m.OutputPackage).filter_by(case_id=case_id).all():
        output.readiness_label = "DRAFT_ONLY"
        output.verification_status = "stale"
    log_event(session, case_id, "decision.invalidated", reason, {"revision": case.assessment_revision})


def snapshot_data(session, case_id):
    session.flush()
    data = {"policy_version": "012.1"}
    types = (m.Case, m.Source, m.NormalizedRequirement, m.ComplianceLedger, m.CVMatch, m.BidScorecard, m.BidRecommendation, m.RiskRegister, m.GapItem, m.ClarificationQuestion, m.ProposalSkeleton, m.MethodologyOutline, m.EGPChecklistItem, m.EvidenceReview)
    for model in types:
        values = []
        for row in session.query(model).filter_by(case_id=case_id).order_by(model.id).all():
            excluded = {"created_at", "updated_at", "uploaded_at"}
            if model is m.Case:
                excluded |= {"status", "readiness_label"}
            item = {}
            for column in model.__table__.columns:
                if column.name in excluded:
                    continue
                value = getattr(row, column.name)
                if isinstance(value, datetime):
                    value = (value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)).isoformat(timespec="microseconds")
                item[column.name] = value
            if model is m.Source:
                item["actual_file_sha256"] = file_hash(row.file_path)
                item["actual_text_sha256"] = file_hash(row.text_extract_path)
            elif model is m.EvidenceReview:
                item["actual_evidence_file_sha256"] = file_hash(row.file_path)
                item["actual_archived_evidence_sha256"] = file_hash(row.archive_file_path)
            values.append(item)
        data[model.__tablename__] = values
    return data


def snapshot_hash(session, case_id):
    return hashlib.sha256(json.dumps(snapshot_data(session, case_id), sort_keys=True, default=str).encode("utf-8")).hexdigest()


def active_sources(session, case_id):
    rows = session.query(m.Source).filter_by(case_id=case_id).all()
    retired = {s.supersedes_source_id for s in rows if s.supersedes_source_id}
    return [s for s in rows if s.source_id not in retired]


def source_review_problem(source):
    actual_text = file_hash(source.text_extract_path)
    actual_file = file_hash(source.file_path) if source.file_path else actual_text
    if source.extraction_status != "extracted" or not actual_text or not actual_file:
        return "blocker", "Source is missing, unreadable or incompletely extracted."
    try:
        if not Path(source.text_extract_path).read_text(encoding="utf-8").strip():
            return "blocker", "Source extraction is empty."
    except (OSError, UnicodeError):
        return "blocker", "Source extraction is unreadable."
    if "limited to first" in (source.notes or "").casefold():
        return "blocker", "Source was only partly processed."
    if (source.content_sha256 and source.content_sha256 != actual_file) or (source.text_sha256 and source.text_sha256 != actual_text):
        return "blocker", "Source bytes changed; register a new version."
    if not source.reviewed_by or not source.reviewed_at or not source.requirements_complete:
        return "warning", "Source and requirement coverage need human review."
    if source.reviewed_sha256 != actual_file or source.reviewed_text_sha256 != actual_text:
        return "blocker", "Source review is stale."
    return None


def latest_evidence_review(session, row):
    return session.query(m.EvidenceReview).filter_by(case_id=row.case_id, compliance_id=row.compliance_id).order_by(m.EvidenceReview.id.desc()).first()


def evidence_review_problem(session, case, row, review):
    if review is None:
        return "warning", "Evidence has no attributable verification record."
    if review.review_status != "verified":
        return "blocker", "Evidence verification is failed or unresolved."
    expected_entity = (case.organization or case.client_name or "").strip().casefold()
    if review.legal_entity.strip().casefold() != expected_entity:
        return "blocker", "Evidence belongs to a different legal entity."
    if review.evidence_text_sha256 != text_hash(row.available_evidence):
        return "blocker", "Evidence text changed after review."
    current_date = today()
    try:
        if review.valid_from and date.fromisoformat(review.valid_from) > current_date:
            return "blocker", "Evidence is not yet valid."
        if review.valid_until and date.fromisoformat(review.valid_until) < current_date:
            return "blocker", "Evidence expired."
    except ValueError:
        return "blocker", "Evidence validity dates are invalid."
    if not review.valid_until and not (review.validity_reason or "").strip():
        return "blocker", "Evidence validity needs an explicit end date or reviewed reason."
    if review.file_path and file_hash(review.file_path) != review.file_sha256:
        return "blocker", "Evidence attachment changed or was removed."
    if review.file_path and (not review.archive_file_path or file_hash(review.archive_file_path) != review.archive_sha256):
        return "blocker", "Archived evidence is missing or altered."
    if review.source_id:
        source = session.query(m.Source).filter_by(case_id=case.case_id, source_id=review.source_id).first()
        if source is None or source.source_id not in {s.source_id for s in active_sources(session, case.case_id)} or source_review_problem(source):
            return "blocker", "Evidence source is missing or not currently reviewed."
    if not review.reviewed_by.strip() or not review.review_notes.strip():
        return "blocker", "Evidence review lacks attribution or rationale."
    return None


def mandatory_state(session, case_id, verified=False):
    case = session.query(m.Case).filter_by(case_id=case_id).first()
    requirements = session.query(m.NormalizedRequirement).filter_by(case_id=case_id, mandatory=True).all()
    unresolved, failed = not requirements, False
    for req in requirements:
        rows = session.query(m.ComplianceLedger).filter_by(case_id=case_id, requirement_id=req.requirement_id).all()
        if req.needs_review or len(rows) != 1:
            unresolved = True
            continue
        row = rows[0]
        review = latest_evidence_review(session, row)
        if review and review.review_status == "failed":
            failed = True
        if row.status != "Met" or evidence_problem(row.available_evidence):
            unresolved = True
        elif verified and evidence_review_problem(session, case, row, review):
            unresolved = True
    return "FAIL" if failed else "UNKNOWN" if unresolved else "PASS"


def policy_assessment(session, case_id):
    session.flush()
    case = session.query(m.Case).filter_by(case_id=case_id).first()
    blockers, warnings = [], []
    if not case:
        return {"eligibility": "UNKNOWN", "blockers": [("CASE-001", "Case does not exist.")], "warnings": []}
    provisional = mandatory_state(session, case_id)
    if provisional != "PASS":
        blockers.append(("ELIG-001", "Mandatory requirements are failed, unreviewed, missing or unresolved."))
    sources = active_sources(session, case_id)
    if not sources:
        blockers.append(("SRC-001", "No source is registered."))
    for source in sources:
        issue = source_review_problem(source)
        if issue:
            (blockers if issue[0] == "blocker" else warnings).append(("SRC-003", f"{source.source_id}: {issue[1]}"))
    for req in session.query(m.NormalizedRequirement).filter_by(case_id=case_id, mandatory=True).all():
        if req.source_id not in {s.source_id for s in sources}:
            blockers.append(("REQ-004", f"{req.requirement_id}: requirement lacks a current source in this case."))
        rows = session.query(m.ComplianceLedger).filter_by(case_id=case_id, requirement_id=req.requirement_id).all()
        if len(rows) == 1 and rows[0].status == "Met":
            row = rows[0]
            issue = evidence_problem(row.available_evidence)
            if issue:
                blockers.append(("EVID-001", f"{req.requirement_id}: {issue}"))
            else:
                problem = evidence_review_problem(session, case, row, latest_evidence_review(session, row))
                if problem:
                    (blockers if problem[0] == "blocker" else warnings).append(("EVID-002", f"{req.requirement_id}: {problem[1]}"))
    for item in session.query(m.EGPChecklistItem).filter_by(case_id=case_id).all():
        if item.status not in {"Met", "Not Applicable"} or not (item.evidence_notes or "").strip():
            blockers.append(("EGP-001", f"{item.item_key}: pending check or missing evidence/exclusion rationale."))
    return {"eligibility": mandatory_state(session, case_id, verified=True), "blockers": blockers, "warnings": warnings}


def latest_current_run(session, case_id, fingerprint):
    return session.query(m.VerificationRun).filter_by(case_id=case_id, snapshot_hash=fingerprint).order_by(m.VerificationRun.id.desc()).first()


def current_approval(session, case_id, fingerprint):
    run = latest_current_run(session, case_id, fingerprint)
    if run is None or not run.technical_passed:
        return None
    approvals = session.query(m.DecisionApproval).filter_by(case_id=case_id, snapshot_hash=fingerprint, revoked_at=None).order_by(m.DecisionApproval.id.desc()).all()
    for approval in approvals:
        origin = session.query(m.VerificationRun).filter_by(case_id=case_id, run_id=approval.verification_run_id, snapshot_hash=fingerprint, technical_passed=True).first()
        if origin:
            return approval
    return None


def output_is_current(output, fingerprint, approval):
    return bool(approval and output.snapshot_hash == fingerprint and output.approval_id == approval.approval_id and output.verification_status == "approved" and output.content_sha256 and file_hash(output.file_path) == output.content_sha256)


def release_context(session, case_id, generating=None):
    policy = policy_assessment(session, case_id)
    fingerprint = snapshot_hash(session, case_id)
    approval = current_approval(session, case_id, fingerprint)
    run = latest_current_run(session, case_id, fingerprint)
    approved = bool(not policy["blockers"] and not policy["warnings"] and policy["eligibility"] == "PASS" and approval and run and run.technical_passed)
    outputs = session.query(m.OutputPackage).filter_by(case_id=case_id).all()
    current = [o for o in outputs if output_is_current(o, fingerprint, approval)]
    report = any(o.output_type in {"markdown_report", "docx_report"} for o in current)
    excel = any(o.output_type == "excel_export" for o in current)
    if policy["blockers"]:
        label = "BLOCKED"
    elif not approved:
        label = "PRELIMINARY"
    elif generating == "report":
        label = "EXPORT_READY" if report and excel else "CLIENT_READY"
    elif report and (excel or generating == "excel"):
        label = "EXPORT_READY"
    elif report:
        label = "CLIENT_READY"
    else:
        label = "PRELIMINARY"
    return {**policy, "snapshot_hash": fingerprint, "approval": approval, "run": run, "approved": approved, "readiness_label": label}
