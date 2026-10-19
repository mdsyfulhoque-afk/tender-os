from pathlib import Path

from docx import Document

from tenderproof.services.report_service import generate_docx_report, generate_markdown_report
from tenderproof.services.sample_data_service import create_demo_case
from tenderproof.models import MethodologyOutline
from tenderproof.services.egp_service import ensure_egp_checklist


def test_markdown_report_is_created(session):
    case = create_demo_case(session)
    path = generate_markdown_report(session, case.case_id)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "TenderProof Rapid Bid Diagnostic" in text


def test_docx_report_is_created(session):
    case = create_demo_case(session)
    path = generate_docx_report(session, case.case_id)
    assert path.exists()
    doc = Document(str(path))
    assert any("TenderProof Rapid Bid Diagnostic" in p.text for p in doc.paragraphs)


def test_readiness_label_appears(session):
    case = create_demo_case(session)
    path = generate_markdown_report(session, case.case_id)
    assert case.readiness_label in path.read_text(encoding="utf-8")


def test_prohibited_phrases_do_not_appear(session):
    case = create_demo_case(session)
    path = generate_markdown_report(session, case.case_id)
    text = path.read_text(encoding="utf-8").lower()
    assert "guaranteed win" not in text
    assert "guaranteed success" not in text


def test_report_includes_methodology_conditions_and_analysis_approach(session):
    case = create_demo_case(session)
    session.add(MethodologyOutline(
        case_id=case.case_id,
        module_order=3,
        module_title="Field interviews",
        data_collection_conditions="Obtain informed consent; conduct interviews in Bangla.",
        analysis_approach="Rules-based NLP (local)",
    ))
    session.flush()
    text = generate_markdown_report(session, case.case_id).read_text(encoding="utf-8")
    assert "Obtain informed consent; conduct interviews in Bangla." in text
    assert "Rules-based NLP (local)" in text


def test_report_includes_egp_readiness_when_activated(session):
    case = create_demo_case(session)
    items = ensure_egp_checklist(session, case.case_id)
    items[0].status = "Met"
    items[0].evidence_notes = "Reviewed against current BPPA notice."
    path = generate_markdown_report(session, case.case_id)
    text = path.read_text(encoding="utf-8")
    assert "Bangladesh e-GP readiness" in text
    assert "Reviewed against current BPPA notice." in text

