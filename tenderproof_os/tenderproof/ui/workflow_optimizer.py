import streamlit as st

from ..services.workflow_service import build_workflow_steps
from .helpers import require_case


def render(session) -> None:
    st.title("Workflow Optimizer")
    case = require_case(session)
    if not case:
        return

    steps = build_workflow_steps(session, case)
    complete = sum(bool(step["complete"]) for step in steps)
    st.progress(complete / len(steps), text=f"{complete} of {len(steps)} workflow steps complete")
    next_step = next((step for step in steps if not step["complete"]), None)
    if next_step:
        st.warning(f"Next action: {next_step['action']}")
        if st.button(f"Open {next_step['page']}", type="primary"):
            st.session_state["workspace_page"] = next_step["page"]
            st.rerun()
    else:
        st.success("All tracked workflow steps are complete. Re-run verification after any further edits.")

    st.dataframe(
        [{"Status": "Complete" if row["complete"] else "Next" if row is next_step else "Pending", "Step": row["step"], "Action": row["action"]} for row in steps],
        use_container_width=True,
        hide_index=True,
    )
