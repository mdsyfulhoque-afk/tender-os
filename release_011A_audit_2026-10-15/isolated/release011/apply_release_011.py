from pathlib import Path

root = Path(__file__).resolve().parent


def patch(relative, old, new):
    path = root / relative
    text = path.read_text(encoding="utf-8")

    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{relative}: expected one patch anchor, found {count}"
        )

    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("PATCHED:", relative)


# 01 — Block positive recommendations when mandatory
# evidence or human review remains unresolved.
patch(
    "tenderproof/services/bid_score_service.py",
    "from ..models import BidRecommendation, BidScorecard",
    "from ..models import (BidRecommendation, BidScorecard, "
    "NormalizedRequirement, ComplianceLedger)",
)

patch(
    "tenderproof/services/bid_score_service.py",
    "    rec_text = recommendation_for_percentage(percentage, missing_inputs)\n",
    """    rec_text = recommendation_for_percentage(percentage, missing_inputs)

    requirements = session.query(NormalizedRequirement).filter_by(
        case_id=case_id, mandatory=True
    ).all()

    compliance = session.query(ComplianceLedger).filter_by(
        case_id=case_id
    ).all()

    by_requirement = {}
    for item in compliance:
        by_requirement.setdefault(item.requirement_id, []).append(item)

    unresolved = not requirements
    failed = False

    for requirement in requirements:
        rows_for_requirement = by_requirement.get(
            requirement.requirement_id, []
        )

        if requirement.needs_review or len(rows_for_requirement) != 1:
            unresolved = True
            continue

        row = rows_for_requirement[0]

        if row.status == "Gap":
            failed = True
        elif (
            row.status != "Met"
            or not (row.available_evidence or "").strip()
        ):
            unresolved = True

    if failed:
        rec_text = "Reject / No-bid"
    elif unresolved:
        rec_text = "Pending input"
""",
)


# 02 — Make unresolved mandatory requirements
# verification blockers.
patch(
    "tenderproof/services/verification_service.py",
    "    gaps = session.query(GapItem).filter(GapItem.case_id == case_id).all()\n",
    """    mandatory = [r for r in reqs if r.mandatory]
    by_requirement = {}
    for item in comp:
        by_requirement.setdefault(item.requirement_id, []).append(item)

    mandatory_ok = bool(mandatory)
    unresolved_reasons = []

    for requirement in mandatory:
        rows = by_requirement.get(requirement.requirement_id, [])

        if requirement.needs_review:
            mandatory_ok = False
            unresolved_reasons.append(
                f"{requirement.requirement_id}: human review pending"
            )

        if len(rows) != 1:
            mandatory_ok = False
            unresolved_reasons.append(
                f"{requirement.requirement_id}: compliance row missing/duplicate"
            )
            continue

        row = rows[0]
        if row.status != "Met" or not (row.available_evidence or "").strip():
            mandatory_ok = False
            unresolved_reasons.append(
                f"{requirement.requirement_id}: mandatory evidence unresolved"
            )

    _add(
        results,
        "ELIG-001",
        "Mandatory eligibility resolved",
        mandatory_ok,
        "blocker",
        (
            "Mandatory evidence and review checks passed."
            if mandatory_ok
            else "Mandatory eligibility blocked: "
                 + "; ".join(unresolved_reasons or ["no mandatory requirements verified"])
        ),
    )

    gaps = session.query(GapItem).filter(GapItem.case_id == case_id).all()
""",
)


# 03 — Invalidate readiness immediately on source registration.
# The source module has two registration paths.
path = root / "tenderproof/services/source_service.py"
text = path.read_text(encoding="utf-8")

old_import = "from ..models import Source"
if text.count(old_import) != 1:
    raise RuntimeError("Unexpected source model import")

text = text.replace(
    old_import,
    "from ..models import Source, Case, OutputPackage, VerificationResult",
    1,
)

helper = '''

def _invalidate_readiness(session: Session, case_id: str) -> None:
    case = session.query(Case).filter_by(case_id=case_id).first()
    if case is None:
        raise ValueError(f"Unknown case: {case_id}")

    case.readiness_label = "DRAFT_ONLY"
    case.status = "draft"

    for output in session.query(OutputPackage).filter_by(
        case_id=case_id
    ).all():
        output.readiness_label = "DRAFT_ONLY"
        output.verification_status = "stale"

    session.query(VerificationResult).filter_by(
        case_id=case_id
    ).delete(synchronize_session=False)

    log_event(
        session, case_id, "verification.invalidated",
        "New source registered; prior readiness requires re-verification."
    )
'''

marker = "\ndef register_manual_text("
if text.count(marker) != 1:
    raise RuntimeError("Unexpected source registration structure")
text = text.replace(marker, helper + marker, 1)

# Both manual text and uploaded-file registration use this
# source insertion sequence.
anchor = "    session.add(source)\n    session.flush()\n"
if text.count(anchor) != 2:
    raise RuntimeError(
        f"Expected two source registration paths; found {text.count(anchor)}"
    )

text = text.replace(
    anchor,
    anchor + "    _invalidate_readiness(session, case_id)\n",
)

path.write_text(text, encoding="utf-8")
print("PATCHED: tenderproof/services/source_service.py")


# 04 — Additional regression tests.
test = root / "tests/test_release_011.py"
if test.exists():
    raise RuntimeError("Regression test file already exists")

test.write_text(
'''from uuid import uuid4

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
''',
    encoding="utf-8",
)

print("CREATED: tests/test_release_011.py")
print("PATCH PREPARATION COMPLETE")