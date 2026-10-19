from pathlib import Path

from tenderproof.models import Case, OutputPackage
from tenderproof.services.compliance_service import auto_create_compliance_rows
from tenderproof.services.extraction_service import create_requirements_from_source
from tenderproof.services.source_service import register_manual_text
from tenderproof.services.verification_service import run_verification


def test_missing_tor_source_fails(session):
    session.add(Case(case_id="TP-NOSRC", client_name="Client", tender_title="Tender"))
    session.flush()
    summary = run_verification(session, "TP-NOSRC")
    assert any(r.rule_code == "SRC-001" and r.status == "failed" for r in summary.rule_results)


def test_missing_requirements_fails(session):
    session.add(Case(case_id="TP-NOREQ", client_name="Client", tender_title="Tender"))
    register_manual_text(session, "TP-NOREQ", "The bidder shall submit a methodology.")
    session.flush()
    summary = run_verification(session, "TP-NOREQ")
    assert any(r.rule_code == "REQ-001" and r.status == "failed" for r in summary.rule_results)


def test_missing_bid_recommendation_blocks_client_ready(session):
    session.add(Case(case_id="TP-NOREC", client_name="Client", tender_title="Tender"))
    source = register_manual_text(session, "TP-NOREC", "The bidder shall submit a methodology.")
    create_requirements_from_source(session, "TP-NOREC", source.source_id)
    auto_create_compliance_rows(session, "TP-NOREC")
    session.flush()
    summary = run_verification(session, "TP-NOREC")
    assert any(r.rule_code == "BID-002" and r.status == "failed" for r in summary.rule_results)


def test_report_with_prohibited_language_fails_safe_001(session, tmp_path):
    session.add(Case(case_id="TP-BADSAFE", client_name="Client", tender_title="Tender"))
    bad_report = tmp_path / "bad.md"
    bad_report.write_text("This is a guaranteed win.", encoding="utf-8")
    session.add(
        OutputPackage(
            output_id="OUT-BADSAFE",
            case_id="TP-BADSAFE",
            output_type="markdown_report",
            file_path=str(bad_report),
            readiness_label="DRAFT_ONLY",
        )
    )
    session.flush()
    summary = run_verification(session, "TP-BADSAFE")
    assert any(r.rule_code == "SAFE-001" and r.status == "failed" for r in summary.rule_results)

