from sqlalchemy import func, select

from tenderproof.db import Base
from tenderproof.models import ClarificationQuestion, RiskRegister
from tenderproof.services.clarification_service import add_clarification_question
from tenderproof.services.risk_service import auto_generate_risks_from_gaps
from tenderproof.services.sample_data_service import create_demo_case


def _row_counts(session) -> dict[str, int]:
    return {
        table.name: session.scalar(select(func.count()).select_from(table))
        for table in Base.metadata.sorted_tables
    }


def test_two_demo_runs_do_not_duplicate_records(session):
    first = create_demo_case(session)
    session.flush()
    before = _row_counts(session)

    second = create_demo_case(session)
    session.flush()
    after = _row_counts(session)

    assert second.case_id == first.case_id
    assert after == before


def test_logical_clarification_and_risk_generation_are_idempotent(session):
    case = create_demo_case(session)
    original_question_count = session.query(ClarificationQuestion).filter_by(case_id=case.case_id).count()
    duplicate = add_clarification_question(
        session,
        case.case_id,
        related_requirement_id="different-reference",
        question="  WILL the donor accept equivalent regional experience for the Team Leader? ",
    )
    assert duplicate.case_id == case.case_id
    assert session.query(ClarificationQuestion).filter_by(case_id=case.case_id).count() == original_question_count

    original_risk_count = session.query(RiskRegister).filter_by(case_id=case.case_id).count()
    auto_generate_risks_from_gaps(session, case.case_id)
    second_generation = auto_generate_risks_from_gaps(session, case.case_id)
    assert second_generation == []
    assert session.query(RiskRegister).filter_by(case_id=case.case_id).count() == original_risk_count
