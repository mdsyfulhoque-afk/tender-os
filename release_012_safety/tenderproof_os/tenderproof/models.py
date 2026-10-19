from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now_utc() -> datetime:
    return datetime.now(UTC)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    client_name: Mapped[str | None] = mapped_column(String(255))
    organization: Mapped[str | None] = mapped_column(String(255))
    contact_person: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255))
    whatsapp: Mapped[str | None] = mapped_column(String(80))
    tender_title: Mapped[str | None] = mapped_column(String(500))
    donor_client: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(120))
    sector: Mapped[str | None] = mapped_column(String(120))
    submission_deadline: Mapped[str | None] = mapped_column(String(80))
    submission_type: Mapped[str | None] = mapped_column(String(120))
    bidding_role: Mapped[str | None] = mapped_column(String(120))
    diagnostic_type: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(80), default="draft")
    payment_status: Mapped[str | None] = mapped_column(String(80), default="unpaid")
    readiness_label: Mapped[str] = mapped_column(String(80), default="DRAFT_ONLY")
    assessment_revision: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    filename: Mapped[str | None] = mapped_column(String(500))
    file_type: Mapped[str | None] = mapped_column(String(80))
    source_category: Mapped[str | None] = mapped_column(String(120))
    file_path: Mapped[str | None] = mapped_column(String(1000))
    text_extract_path: Mapped[str | None] = mapped_column(String(1000))
    extraction_status: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    content_sha256: Mapped[str | None] = mapped_column(String(64))
    text_sha256: Mapped[str | None] = mapped_column(String(64))
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    supersedes_source_id: Mapped[str | None] = mapped_column(String(80))
    reviewed_sha256: Mapped[str | None] = mapped_column(String(64))
    reviewed_text_sha256: Mapped[str | None] = mapped_column(String(64))
    reviewed_by: Mapped[str | None] = mapped_column(String(255))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    review_notes: Mapped[str | None] = mapped_column(Text)
    requirements_complete: Mapped[bool] = mapped_column(Boolean, default=False)


class NormalizedRequirement(Base):
    __tablename__ = "normalized_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    source_id: Mapped[str | None] = mapped_column(String(80), index=True)
    tor_section_page: Mapped[str | None] = mapped_column(String(255))
    requirement_category: Mapped[str | None] = mapped_column(String(120))
    requirement_text: Mapped[str] = mapped_column(Text)
    atomic_requirement_text: Mapped[str] = mapped_column(Text)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    interpretation: Mapped[str | None] = mapped_column(Text)
    evidence_needed: Mapped[str | None] = mapped_column(Text)
    proposal_section_affected: Mapped[str | None] = mapped_column(String(255))
    expert_role_affected: Mapped[str | None] = mapped_column(String(255))
    deliverable_affected: Mapped[str | None] = mapped_column(String(255))
    evaluation_weight: Mapped[str | None] = mapped_column(String(80))
    form_annex_required: Mapped[str | None] = mapped_column(String(120))
    clarification_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[str | None] = mapped_column(String(80), default="medium")
    match_key: Mapped[str] = mapped_column(String(120), index=True)
    canonical_anchor: Mapped[str] = mapped_column(String(255), index=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class ComplianceLedger(Base):
    __tablename__ = "compliance_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    compliance_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    requirement_id: Mapped[str] = mapped_column(String(80), index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    evidence_needed: Mapped[str | None] = mapped_column(Text)
    available_evidence: Mapped[str | None] = mapped_column(Text)
    gap: Mapped[str | None] = mapped_column(Text)
    proposal_location: Mapped[str | None] = mapped_column(String(255))
    responsible_person: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(80), default="Pending Input")
    risk_level: Mapped[str | None] = mapped_column(String(80), default="medium")
    action_required: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[str | None] = mapped_column(String(80))
    final_check: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class CVMatch(Base):
    __tablename__ = "cv_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    expert_match_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    requirement_id: Mapped[str | None] = mapped_column(String(80), index=True)
    expert_role: Mapped[str | None] = mapped_column(String(255))
    candidate_name: Mapped[str | None] = mapped_column(String(255))
    required_qualification: Mapped[str | None] = mapped_column(Text)
    required_years: Mapped[str | None] = mapped_column(String(80))
    required_specific_experience: Mapped[str | None] = mapped_column(Text)
    required_country_region_experience: Mapped[str | None] = mapped_column(Text)
    required_donor_experience: Mapped[str | None] = mapped_column(Text)
    required_language_tools: Mapped[str | None] = mapped_column(Text)
    cv_evidence: Mapped[str | None] = mapped_column(Text)
    match_score_1_to_5: Mapped[int | None] = mapped_column(Integer)
    gap: Mapped[str | None] = mapped_column(Text)
    rewrite_needed: Mapped[bool] = mapped_column(Boolean, default=False)
    suggested_cv_language: Mapped[str | None] = mapped_column(Text)
    replace_candidate: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_level: Mapped[str | None] = mapped_column(String(80), default="medium")
    notes: Mapped[str | None] = mapped_column(Text)


class BidScorecard(Base):
    __tablename__ = "bid_scorecard"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    category: Mapped[str] = mapped_column(String(120))
    score: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=5)
    rationale: Mapped[str | None] = mapped_column(Text)
    evidence_or_gap_reference: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class BidRecommendation(Base):
    __tablename__ = "bid_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=50)
    percentage: Mapped[float] = mapped_column(Float, default=0)
    recommendation: Mapped[str] = mapped_column(String(120), default="Pending input")
    rationale: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class RiskRegister(Base):
    __tablename__ = "risk_register"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    risk_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    risk_category: Mapped[str | None] = mapped_column(String(120))
    risk_description: Mapped[str | None] = mapped_column(Text)
    source_requirement_id: Mapped[str | None] = mapped_column(String(80))
    severity: Mapped[str | None] = mapped_column(String(80), default="medium")
    likelihood: Mapped[str | None] = mapped_column(String(80), default="medium")
    mitigation: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(255))
    due_date: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str | None] = mapped_column(String(80), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class GapItem(Base):
    __tablename__ = "gap_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gap_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    related_requirement_id: Mapped[str | None] = mapped_column(String(80))
    related_compliance_id: Mapped[str | None] = mapped_column(String(80))
    related_cv_match_id: Mapped[str | None] = mapped_column(String(80))
    gap_type: Mapped[str | None] = mapped_column(String(120))
    gap_description: Mapped[str | None] = mapped_column(Text)
    required_action: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(255))
    due_date: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str | None] = mapped_column(String(80), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class ClarificationQuestion(Base):
    __tablename__ = "clarification_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    related_requirement_id: Mapped[str | None] = mapped_column(String(80))
    question: Mapped[str | None] = mapped_column(Text)
    why_it_matters: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str | None] = mapped_column(String(80), default="medium")
    status: Mapped[str | None] = mapped_column(String(80), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class ProposalSkeleton(Base):
    __tablename__ = "proposal_skeleton"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    section_order: Mapped[int] = mapped_column(Integer, default=1)
    section_title: Mapped[str | None] = mapped_column(String(255))
    purpose: Mapped[str | None] = mapped_column(Text)
    required_inputs: Mapped[str | None] = mapped_column(Text)
    linked_requirements: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class MethodologyOutline(Base):
    __tablename__ = "methodology_outline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    module_order: Mapped[int] = mapped_column(Integer, default=1)
    module_title: Mapped[str | None] = mapped_column(String(255))
    module_description: Mapped[str | None] = mapped_column(Text)
    linked_requirements: Mapped[str | None] = mapped_column(Text)
    evidence_needed: Mapped[str | None] = mapped_column(Text)
    data_collection_conditions: Mapped[str | None] = mapped_column(Text)
    analysis_approach: Mapped[str | None] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str | None] = mapped_column(String(80), index=True)
    event_type: Mapped[str | None] = mapped_column(String(120))
    event_message: Mapped[str | None] = mapped_column(Text)
    event_payload_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    verification_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    rule_code: Mapped[str] = mapped_column(String(80))
    rule_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(80))
    message: Mapped[str | None] = mapped_column(Text)
    blocker: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    run_id: Mapped[str | None] = mapped_column(String(80), index=True)


class IPCapture(Base):
    __tablename__ = "ip_capture"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    donor: Mapped[str | None] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(120))
    pattern_type: Mapped[str | None] = mapped_column(String(120))
    pattern_title: Mapped[str | None] = mapped_column(String(255))
    pattern_description: Mapped[str | None] = mapped_column(Text)
    reusable_asset: Mapped[str | None] = mapped_column(Text)
    anonymized: Mapped[bool] = mapped_column(Boolean, default=True)
    confidence_level: Mapped[str | None] = mapped_column(String(80), default="medium")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class OutputPackage(Base):
    __tablename__ = "output_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    output_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    output_type: Mapped[str] = mapped_column(String(120))
    file_path: Mapped[str] = mapped_column(String(1000))
    readiness_label: Mapped[str] = mapped_column(String(80), default="DRAFT_ONLY")
    verification_status: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    snapshot_hash: Mapped[str | None] = mapped_column(String(64))
    approval_id: Mapped[str | None] = mapped_column(String(80))
    verification_run_id: Mapped[str | None] = mapped_column(String(80))
    content_sha256: Mapped[str | None] = mapped_column(String(64))


class EGPChecklistItem(Base):
    __tablename__ = "egp_checklist_items"
    __table_args__ = (UniqueConstraint("case_id", "item_key", name="uq_egp_check_case_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    checklist_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    case_id: Mapped[str] = mapped_column(String(80), index=True)
    item_key: Mapped[str] = mapped_column(String(120))
    stage: Mapped[str] = mapped_column(String(80))
    item_title: Mapped[str] = mapped_column(String(500))
    guidance: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(80), default="Pending Input")
    evidence_notes: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, onupdate=now_utc)


class EvidenceReview(Base):
    __tablename__ = "evidence_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evidence_id: Mapped[str] = mapped_column(String(80), unique=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    requirement_id: Mapped[str] = mapped_column(String(80), index=True)
    compliance_id: Mapped[str] = mapped_column(String(80), index=True)
    evidence_text_sha256: Mapped[str] = mapped_column(String(64))
    source_id: Mapped[str | None] = mapped_column(String(80))
    file_path: Mapped[str | None] = mapped_column(Text)
    file_sha256: Mapped[str | None] = mapped_column(String(64))
    archive_file_path: Mapped[str | None] = mapped_column(Text)
    archive_sha256: Mapped[str | None] = mapped_column(String(64))
    legal_entity: Mapped[str] = mapped_column(String(255))
    valid_from: Mapped[str | None] = mapped_column(String(10))
    valid_until: Mapped[str | None] = mapped_column(String(10))
    validity_reason: Mapped[str | None] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(String(40))
    reviewed_by: Mapped[str] = mapped_column(String(255))
    review_notes: Mapped[str] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(80), unique=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    snapshot_hash: Mapped[str] = mapped_column(String(64))
    snapshot_json: Mapped[str] = mapped_column(Text)
    technical_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    overall_status: Mapped[str] = mapped_column(String(40))
    readiness_label: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class DecisionApproval(Base):
    __tablename__ = "decision_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    approval_id: Mapped[str] = mapped_column(String(80), unique=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id"), index=True)
    snapshot_hash: Mapped[str] = mapped_column(String(64))
    verification_run_id: Mapped[str] = mapped_column(String(80))
    approved_by: Mapped[str] = mapped_column(String(255))
    rationale: Mapped[str] = mapped_column(Text)
    approved_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    revocation_reason: Mapped[str | None] = mapped_column(Text)


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"

    version: Mapped[str] = mapped_column(String(80), primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
