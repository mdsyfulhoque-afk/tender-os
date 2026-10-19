from pathlib import Path
from sqlalchemy.exc import IntegrityError

import pandas as pd
from sqlalchemy.orm import Session

from ..config import SEED_DIR, ensure_directories
from ..constants import REQUIRED_BID_CATEGORIES
from ..models import Case, ComplianceLedger, MethodologyOutline, ProposalSkeleton
from .bid_score_service import save_scores_and_recommendation
from .case_service import create_case
from .clarification_service import add_clarification_question
from .compliance_service import auto_create_compliance_rows, update_compliance_row
from .cv_match_service import add_cv_match
from .extraction_service import create_requirements_from_source
from .ip_capture_service import add_ip_capture
from .risk_service import auto_generate_risks_from_gaps
from .source_service import register_manual_text


DEMO_TOR_TEXT = """
The Consultant shall submit a technical proposal including methodology, workplan, quality assurance approach, and team organization.
The proposal must include a Team Leader with at least 10 years of donor-funded project management experience.
The bidder must provide CVs for all key experts showing relevant country and sector experience.
The bidder shall submit completed administrative forms and signed declarations in the required annexes.
The methodology must include stakeholder consultation, data collection, validation, and final reporting steps.
The assignment requires delivery of inception report, draft report, validation workshop, and final report.
All proposals must be submitted before the stated deadline using the donor portal.
"""


DEMO_CLIENT_NAME = "Demo Consulting Ltd."
DEMO_TENDER_TITLE = "Donor-funded Evaluation and Learning Assignment"


def create_demo_case(session: Session):
    existing = (
        session.query(Case)
        .filter_by(client_name=DEMO_CLIENT_NAME, tender_title=DEMO_TENDER_TITLE)
        .order_by(Case.created_at.asc())
        .first()
    )
    if existing:
        return existing

    try:
        with session.begin_nested():
            return _build_demo_case(session)
    except IntegrityError:
        # Another request may have created the same demo while this one was running.
        existing = (
            session.query(Case)
            .filter_by(client_name=DEMO_CLIENT_NAME, tender_title=DEMO_TENDER_TITLE)
            .order_by(Case.created_at.asc())
            .first()
        )
        if existing:
            return existing
        raise


def _build_demo_case(session: Session):
    case = create_case(
        session,
        client_name=DEMO_CLIENT_NAME,
        organization=DEMO_CLIENT_NAME,
        contact_person="Syful Islam",
        email="demo@example.com",
        whatsapp="+880000000000",
        tender_title=DEMO_TENDER_TITLE,
        donor_client="International Development Donor",
        country="Bangladesh",
        sector="Monitoring, Evaluation and Learning",
        submission_deadline="2026-07-15",
        submission_type="Technical + Financial",
        bidding_role="Lead bidder",
        diagnostic_type="TenderProof Rapid Bid Diagnostic",
        payment_status="paid",
    )
    source = register_manual_text(session, case.case_id, DEMO_TOR_TEXT)
    reqs = create_requirements_from_source(session, case.case_id, source.source_id)
    auto_create_compliance_rows(session, case.case_id)
    for row in session.query(ComplianceLedger).filter_by(case_id=case.case_id).all()[:2]:
        update_compliance_row(session, row.compliance_id, status="Met", available_evidence="Existing organizational profile and prior donor project evidence.", gap="")
    add_cv_match(
        session,
        case.case_id,
        requirement_id=reqs[1].requirement_id if len(reqs) > 1 else "",
        expert_role="Team Leader",
        candidate_name="Amina Rahman",
        required_years="10",
        required_donor_experience="Donor-funded evaluation management",
        cv_evidence="Led three donor-funded evaluations in Bangladesh and Nepal between 2019 and 2025.",
        match_score_1_to_5=4,
        rewrite_needed=True,
    )
    scores = {category: {"score": 4 if category not in {"competition risk", "compliance risk"} else 3, "rationale": "Demo score.", "evidence_or_gap_reference": "Demo case"} for category in REQUIRED_BID_CATEGORIES}
    save_scores_and_recommendation(session, case.case_id, scores)
    session.add(ProposalSkeleton(case_id=case.case_id, section_order=1, section_title="Understanding of Assignment", purpose="Show interpretation of donor objectives.", required_inputs="ToR objectives and context", linked_requirements="all"))
    session.add(ProposalSkeleton(case_id=case.case_id, section_order=2, section_title="Methodology", purpose="Describe delivery approach.", required_inputs="Consultation, data collection, validation plan", linked_requirements="methodology requirements"))
    session.add(MethodologyOutline(case_id=case.case_id, module_order=1, module_title="Inception and Workplan", module_description="Kickoff, document review, and detailed workplan.", linked_requirements="REQ", evidence_needed="Workplan evidence"))
    session.add(MethodologyOutline(case_id=case.case_id, module_order=2, module_title="Data Collection and Validation", module_description="Stakeholder interviews, analysis, and validation workshop.", linked_requirements="REQ", evidence_needed="Methodology notes"))
    add_clarification_question(
        session,
        case.case_id,
        related_requirement_id=reqs[0].requirement_id if reqs else "",
        question="Will the donor accept equivalent regional experience for the Team Leader?",
        why_it_matters="It affects CV compliance risk.",
        priority="high",
    )
    auto_generate_risks_from_gaps(session, case.case_id)
    add_ip_capture(
        session,
        case.case_id,
        donor="International Development Donor",
        sector="MEL",
        country="Bangladesh",
        pattern_type="CV scoring pattern",
        pattern_title="Team Leader donor experience threshold",
        pattern_description="Team Leader requirements often combine years, donor experience, and country experience.",
        reusable_asset="Use CV evidence table with years, donor, country, and assignment role columns.",
    )
    session.flush()
    return case


def create_seed_csvs() -> None:
    ensure_directories()
    samples = {
        "leads.csv": [{"organization": "Demo Consulting Ltd.", "contact": "Syful Islam", "status": "warm", "offer": "Rapid Bid Diagnostic"}],
        "tender_opportunities.csv": [{"title": "Donor-funded Evaluation and Learning Assignment", "donor": "International Development Donor", "deadline": "2026-07-15"}],
        "client_intake.csv": [{"client_name": "Demo Consulting Ltd.", "diagnostic_type": "Rapid Bid Diagnostic", "payment_status": "paid"}],
        "tor_extraction.csv": [{"requirement_category": "methodology", "atomic_requirement_text": "Submit methodology and workplan.", "mandatory": True}],
        "compliance_matrix.csv": [{"status": "Pending Input", "evidence_needed": "Technical proposal section"}],
        "cv_matcher.csv": [{"expert_role": "Team Leader", "candidate_name": "Amina Rahman", "match_score_1_to_5": 4}],
        "bid_no_bid_scorecard.csv": [{"category": cat, "score": 4, "max_score": 5} for cat in REQUIRED_BID_CATEGORIES],
        "risk_register.csv": [{"risk_category": "compliance", "severity": "high", "risk_description": "Missing annex evidence"}],
        "gap_items.csv": [{"gap_type": "compliance", "gap_description": "Pending signed declaration"}],
        "clarification_questions.csv": [{"question": "Will equivalent regional experience be accepted?", "priority": "high"}],
        "proposal_skeleton.csv": [{"section_order": 1, "section_title": "Understanding of Assignment"}],
        "methodology_outline.csv": [{"module_order": 1, "module_title": "Inception and Workplan"}],
        "ip_capture.csv": [{"pattern_type": "ToR pattern", "pattern_title": "CV evidence threshold"}],
    }
    for filename, rows in samples.items():
        path = SEED_DIR / filename
        if not path.exists():
            pd.DataFrame(rows).to_csv(path, index=False)
