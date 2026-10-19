# Clarification Questions Prompt

Generate donor clarification questions from requirements, gaps, and risks.

Rules:
- Do not invent evidence.
- Mark missing evidence as Gap or Pending Input.
- Preserve ToR references.
- Separate facts from recommendations.
- Never guarantee tender wins.
- Output structured tables where possible.
- Ask for human review where uncertain.

Required output columns:
- Related requirement ID
- Question
- Why it matters
- Priority
- Status

