# Compliance Matrix Review Prompt

Review the normalized ToR requirements against available client evidence.

Rules:
- Do not invent evidence.
- Mark missing evidence as Gap or Pending Input.
- Preserve ToR references.
- Separate facts from recommendations.
- Never guarantee tender wins.
- Output structured tables where possible.
- Ask for human review where uncertain.

Required output columns:
- Requirement ID
- Evidence needed
- Available evidence
- Status: Met / Partially Met / Gap / Pending Input / Not Applicable
- Proposal location
- Responsible person
- Risk level
- Action required
- Notes

