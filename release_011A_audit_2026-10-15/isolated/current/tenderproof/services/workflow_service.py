from pathlib import Path

from sqlalchemy.orm import Session

from ..models import (
    BidRecommendation,
    Case,
    ComplianceLedger,
    CVMatch,
    EGPChecklistItem,
    MethodologyOutline,
    NormalizedRequirement,
    OutputPackage,
    RiskRegister,
    Source,
    VerificationResult,
)


def build_workflow_steps(session: Session, case: Case) -> list[dict[str, str | bool]]:
    sources = session.query(Source).filter_by(case_id=case.case_id).all()
    requirements = session.query(NormalizedRequirement).filter_by(case_id=case.case_id).count()
    compliance = session.query(ComplianceLedger).filter_by(case_id=case.case_id).count()
    cvs = session.query(CVMatch).filter_by(case_id=case.case_id).count()
    recommendation = session.query(BidRecommendation).filter_by(case_id=case.case_id).count()
    risks = session.query(RiskRegister).filter_by(case_id=case.case_id).count()
    methodology = session.query(MethodologyOutline).filter_by(case_id=case.case_id).count()
    outputs = session.query(OutputPackage).filter_by(case_id=case.case_id).all()
    report = any(o.output_type in {"markdown_report", "docx_report"} and Path(o.file_path).exists() for o in outputs)
    excel = any(o.output_type == "excel_export" and Path(o.file_path).exists() for o in outputs)
    verified = session.query(VerificationResult).filter_by(case_id=case.case_id).count() > 0
    steps = [
        _step("Register ToR/source", bool(sources), "Upload / Register Inputs", "Add a source document or paste ToR text."),
        _step("Extract requirements", requirements > 0, "ToR Extraction", "Normalize ToR clauses and review source anchors."),
        _step("Map compliance", compliance > 0, "Compliance Matrix", "Create compliance rows and record evidence or gaps."),
        _step("Match experts", cvs > 0, "CV Matcher", "Record candidate evidence against expert requirements."),
        _step("Make bid decision", recommendation > 0, "Bid/No-Bid Scorecard", "Complete all scorecard categories and recommendation."),
        _step("Build method and risk plan", methodology > 0 and risks > 0, "Proposal Skeleton and Methodology", "Document collection conditions, approach, and delivery risks."),
        _step("Generate diagnostic report", report, "Diagnostic Report Generator", "Generate and review Markdown or DOCX output."),
        _step("Export workbook", excel, "Excel Export", "Create the case workbook for review and handoff."),
        _step("Run verification", verified, "Verification / Audit Log", "Run readiness checks after the latest changes."),
    ]
    egp_items = session.query(EGPChecklistItem).filter_by(case_id=case.case_id).all()
    if egp_items:
        resolved = all(item.status in {"Met", "Not Applicable"} for item in egp_items)
        steps.insert(1, _step(
            "Review Bangladesh e-GP readiness",
            resolved,
            "Bangladesh e-GP Readiness",
            "Resolve applicable e-GP checks and verify each one against the live tender document.",
        ))
    return steps


def _step(title: str, complete: bool, page: str, action: str) -> dict[str, str | bool]:
    return {"step": title, "complete": complete, "page": page, "action": action}
