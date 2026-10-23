# TenderOS / TenderProof OS / ProposalGuard

A local Python/Streamlit workspace for evidence-based tender and proposal diagnostics. Each tender is a case connecting source documents, requirements, compliance, expert evidence, bid decisions, risks, methodology, verification and outputs.

## New TenderOS portal — owner workstation development

The additive v1.4 development platform is in `apps/web/`. It connects customer and internal workflows to a private Knowledge Engine that stays **outside this Git repository and outside OneDrive** on the owner's computer. The public repository contains the portal, durable broker and public transport contracts. No private engine implementation, rules, prompts, model weights, keys or new customer runtime data are published.

This edition is **PILOT_PC**, with preliminary diagnostics and draft managed work. Payments, public hosting and formal final release are disabled. It is not a paid production service. [Implementation status and remaining gates](docs/TenderOS_v14_Development_Status.md).

Requirements: Node 24.16 or later; the private node is separately provisioned by its owner. On Windows:

```powershell
npm install
npm run setup:local
npm run build
.\Start-TenderOS.ps1
```

Open **http://127.0.0.1:3414**. Owner login details are generated locally in `%LOCALAPPDATA%\TenderOS\public-platform\OWNER_LOGIN.txt`; the password is never committed. Customer registration grants no internal staff rights. The original Streamlit app remains separate.

For source editing, use `.\Start-TenderOS.ps1 -Development`. Stop this checkout's web/node processes using `.\Stop-TenderOS.ps1`. Startup binds to loopback only. The private engine source/runtime is under `%USERPROFILE%\TenderOS-Private\private-engine`, never downloaded from this repository. If it is not provisioned, the public portal reports it offline. Public API/crypto interoperability is described in [the development contract](packages/contracts/README.md).

Create a case, verify the local node fingerprint, confirm processing permission, add encrypted documents and request a private analysis. The fictional example documents are for learning the workflow; they are not approved benchmarks or real credentials. Keep the initiating browser profile: it holds non-extractable recipient keys for encrypted reports.

Before publishing changes, stage public files explicitly and run `npm run publish:check`. Uploaded engineering source documents, private material, runtime databases, dependencies and generated build output are excluded by `.gitignore`.

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
