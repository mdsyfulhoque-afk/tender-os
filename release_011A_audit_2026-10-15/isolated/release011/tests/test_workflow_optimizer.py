from tenderproof.services.case_service import create_case
from tenderproof.services.workflow_service import build_workflow_steps


def test_workflow_optimizer_starts_with_source_intake(session):
    case = create_case(session, client_name="Workflow Test", tender_title="Test ToR")
    steps = build_workflow_steps(session, case)
    assert steps[0]["step"] == "Register ToR/source"
    assert steps[0]["complete"] is False
    assert steps[0]["page"] == "Upload / Register Inputs"


def test_workflow_optimizer_detects_existing_source(session):
    from tenderproof.services.source_service import register_manual_text

    case = create_case(session, client_name="Workflow Test", tender_title="Test ToR")
    register_manual_text(session, case.case_id, "The bidder shall submit a methodology.")
    steps = build_workflow_steps(session, case)
    assert steps[0]["complete"] is True
    assert steps[1]["complete"] is False
