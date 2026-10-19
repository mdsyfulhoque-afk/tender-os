from uuid import uuid4

import pytest

from tenderproof.constants import REQUIRED_BID_CATEGORIES
from tenderproof.models import (
    Case, ComplianceLedger, NormalizedRequirement
)
from tenderproof.services.bid_score_service import (
    save_scores_and_recommendation
)
from tenderproof.services.source_service import register_manual_text
from tenderproof.services.verification_service import run_verification


def case_with_requirement(session, status, evidence="", reviewed=True):
    suffix = uuid4().hex[:10]
    cid = "PG-011-" + suffix

    case = Case(
        case_id=cid,
        tender_title="Synthetic Tender",
        client_name="Synthetic Client",
    )

    req = NormalizedRequirement(
        requirement_id="REQ-" + suffix,
        case_id=cid,
        source_id="SRC-TEST",
        requirement_text="A valid license is mandatory.",
        atomic_requirement_text="A valid license is mandatory.",
        mandatory=True,
        needs_review=not reviewed,
        match_key="MATCH-" + suffix,
        canonical_anchor="SRC-TEST:1",
    )

    row = ComplianceLedger(
        compliance_id="COMP-" + suffix,
        requirement_id=req.requirement_id,
        case_id=cid,
        status=status,
        available_evidence=evidence,
    )

    session.add_all([case, req, row])
    session.flush()
    return case


def score_all(session, case):
    scores = {
        category: {
            "score": 5,
            "rationale": "Synthetic test",
            "evidence_or_gap_reference": "TEST",
        }
        for category in REQUIRED_BID_CATEGORIES
    }
    return save_scores_and_recommendation(
        session, case.case_id, scores
    )


@pytest.mark.parametrize("status", ["Gap", "Pending Input"])
def test_unresolved_mandatory_never_pursue(session, status):
    case = case_with_requirement(session, status)
    rec = score_all(session, case)
    assert rec.recommendation not in {
        "Pursue", "Pursue with partner",
        "Pursue only as sub-consultant"
    }


def test_unreviewed_requirement_blocks_positive_rec(session):
    case = case_with_requirement(
        session, "Met", "Synthetic evidence", reviewed=False
    )
    rec = score_all(session, case)
    assert rec.recommendation == "Pending input"


def test_valid_record_can_receive_positive_score(session):
    case = case_with_requirement(
        session, "Met", "Synthetic evidence", reviewed=True
    )
    rec = score_all(session, case)
    assert rec.recommendation == "Pursue"


def test_mandatory_gap_blocks_verification(session):
    case = case_with_requirement(session, "Gap")
    score_all(session, case)
    result = run_verification(session, case.case_id)
    assert result.readiness_label == "BLOCKED"
    assert any(
        rule.rule_code == "ELIG-001" and rule.blocker
        for rule in result.rule_results
    )


def test_unreviewed_requirement_blocks_verification(session):
    case = case_with_requirement(
        session, "Met", "Synthetic evidence", reviewed=False
    )
    score_all(session, case)
    result = run_verification(session, case.case_id)
    assert result.readiness_label == "BLOCKED"


def test_new_source_invalidates_readiness(session):
    case = case_with_requirement(session, "Met", "Evidence")
    case.readiness_label = "CLIENT_READY"
    session.flush()

    register_manual_text(
        session,
        case.case_id,
        "Amendment: new mandatory financial requirement.",
        filename="amendment.txt",
    )

    assert case.readiness_label == "DRAFT_ONLY"
