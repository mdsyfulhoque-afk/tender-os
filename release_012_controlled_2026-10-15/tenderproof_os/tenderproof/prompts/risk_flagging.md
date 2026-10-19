# Risk Flagging Prompt

Identify proposal, compliance, CV, delivery, deadline, and strategic bid risks.

Rules:
- Do not invent evidence.
- Mark missing evidence as Gap or Pending Input.
- Preserve ToR references.
- Separate facts from recommendations.
- Never guarantee tender wins.
- Output structured tables where possible.
- Ask for human review where uncertain.

Required output columns:
- Risk category
- Risk description
- Source requirement ID
- Severity
- Likelihood
- Mitigation
- Owner
- Due date
- Status

