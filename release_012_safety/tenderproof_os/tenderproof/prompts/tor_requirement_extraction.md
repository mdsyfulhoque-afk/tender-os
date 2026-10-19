# ToR Requirement Extraction Prompt

Extract donor tender requirements from the provided ToR text.

Rules:
- Do not invent evidence.
- Mark missing evidence as Gap or Pending Input.
- Preserve ToR references, section numbers, page numbers, annex references, and exact wording where possible.
- Separate facts from recommendations.
- Never guarantee tender wins.
- Output structured tables where possible.
- Ask for human review where uncertain.

Required output columns:
- ToR reference
- Requirement category
- Original requirement text
- Atomic requirement
- Mandatory?
- Evidence needed
- Proposal section affected
- Expert role affected
- Risk level
- Clarification needed?
- Human review note

