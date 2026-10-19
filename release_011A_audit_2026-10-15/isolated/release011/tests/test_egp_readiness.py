from tenderproof.services.egp_service import ensure_egp_checklist, update_egp_checklist
from tenderproof.services.workflow_service import build_workflow_steps
from tenderproof.services.case_service import create_case


def test_egp_checklist_seeding_is_idempotent(session):
    case = create_case(session, client_name="Bangladesh Bidder", country="Bangladesh")
    first = ensure_egp_checklist(session, case.case_id)
    second = ensure_egp_checklist(session, case.case_id)
    assert len(first) == 19
    assert len(second) == len(first)
    assert len({item.item_key for item in second}) == len(second)


def test_checklist_updates_persist_and_surface_in_workflow(session):
    case = create_case(session, client_name="Bangladesh Bidder", country="Bangladesh")
    items = ensure_egp_checklist(session, case.case_id)
    target = items[0]
    update_egp_checklist(session, case.case_id, [{
        "item_key": target.item_key,
        "status": "Met",
        "evidence_notes": "Confirmed against current notice.",
    }])
    session.flush()
    refreshed = ensure_egp_checklist(session, case.case_id)
    assert refreshed[0].status == "Met"
    assert refreshed[0].evidence_notes == "Confirmed against current notice."
    step = next(step for step in build_workflow_steps(session, case) if step["step"] == "Review Bangladesh e-GP readiness")
    assert step["complete"] is False
    assert step["page"] == "Bangladesh e-GP Readiness"
