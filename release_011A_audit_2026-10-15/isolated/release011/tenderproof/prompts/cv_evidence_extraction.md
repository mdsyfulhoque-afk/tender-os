# CV Evidence Extraction Prompt

Extract evidence from the provided CV text for the linked expert requirement.

Rules:
- Do not invent evidence.
- Mark missing evidence as Gap or Pending Input.
- Preserve ToR references.
- Separate facts from recommendations.
- Never guarantee tender wins.
- Output structured tables where possible.
- Ask for human review where uncertain.

Required output columns:
- Expert role
- Candidate name
- Requirement
- CV evidence quoted or paraphrased from provided CV only
- Years of experience evidence
- Country/region evidence
- Donor evidence
- Language/tools evidence
- Gap
- Match score 1-5
- Human review note

