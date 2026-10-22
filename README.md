# TenderOS / TenderProof OS / ProposalGuard

A local Python/Streamlit workspace for evidence-based tender and proposal diagnostics. Each tender is a case connecting source documents, requirements, compliance, expert evidence, bid decisions, risks, methodology, verification and outputs.

## Start here

- [Architecture explained in Bangla-English](docs/TenderOS_Architecture_Bangla_English_2026-10-22.md)
- [Original application README](tenderproof_os/README.md)
- [Original application quickstart](tenderproof_os/QUICKSTART.md)
- [Tenderly-to-TenderOS concept map](docs/concept-map-tenderly-to-tenderos.docx) and [PDF](docs/concept-map-tenderly-to-tenderos.pdf)

## Application and review copies

`tenderproof_os/` is the preserved original application. `release_012_safety/` and `release_012_controlled_2026-10-15/` contain isolated Release 012 work, review artifacts and historical verification records. They must not be mistaken for an already integrated operational installation.

The controlled candidate's recorded test summary reports 121 regression checks and a separate 24 safety checks passed. These are historical results inspected on 22 October 2026, not tests rerun for this documentation update. The earlier STOP_REPORT is retained as history; read the subsequent evidence and review runbook together.

- [Controlled candidate operator review](release_012_controlled_2026-10-15/OPERATOR_REVIEW_RUNBOOK.md)
- [Recorded test summary](release_012_controlled_2026-10-15/evidence/test_summary.json)
- [Recovery and integration boundaries](release_012_controlled_2026-10-15/RECOVERY_AND_INTEGRATION_REVIEW.md)
- [Final preservation and approval boundary](release_012_controlled_2026-10-15/evidence/final_boundary.json)

Operational integration and release approval remain pending in those records. Pushing this repository preserves project work; it does not install the candidate, migrate the operational database or approve a tender case.

The concept map and its review PDFs/page images are design artifacts. Its proposed capabilities, including saved bid scenarios and automated monitoring, are roadmap ideas rather than a statement that those features are implemented. `create_concept_map.py` creates the DOCX and requires `python-docx`; PDF and page-image rendering are separate steps.

Local databases, client uploads, generated client reports and credentials are excluded by `.gitignore`. Keep them in the local working environment and its managed backups.
