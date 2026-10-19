from tenderproof.models import ComplianceLedger, NormalizedRequirement
from tenderproof.services.compliance_service import update_compliance_row
from tenderproof.services.gap_service import sync_gaps_from_compliance
from tenderproof.services.tor_normalizer import generate_canonical_anchor, generate_match_key


def test_mandatory_requirement_without_evidence_creates_gapitem(session):
    req = NormalizedRequirement(
        requirement_id="REQ-GAP-1",
        case_id="TP-GAP",
        source_id="SRC",
        tor_section_page="1",
        requirement_category="methodology",
        requirement_text="Submit methodology.",
        atomic_requirement_text="Submit methodology.",
        mandatory=True,
        match_key=generate_match_key("TP-GAP", "methodology", "1", "Submit methodology."),
        canonical_anchor=generate_canonical_anchor("SRC", "1", 1),
    )
    row = ComplianceLedger(
        compliance_id="COMP-GAP-1",
        requirement_id=req.requirement_id,
        case_id="TP-GAP",
        status="Met",
        available_evidence="",
        gap="",
    )
    session.add_all([req, row])
    session.flush()
    created = sync_gaps_from_compliance(session, "TP-GAP")
    assert created


def test_pending_input_row_creates_gapitem(session):
    row = ComplianceLedger(
        compliance_id="COMP-GAP-2",
        requirement_id="REQ-GAP-2",
        case_id="TP-GAP",
        status="Pending Input",
        gap="Missing annex.",
    )
    session.add(row)
    session.flush()
    created = sync_gaps_from_compliance(session, "TP-GAP")
    assert created[0].gap_type == "compliance"

