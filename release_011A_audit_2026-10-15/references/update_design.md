# Proposal Guard → e-GP Tender-to-Fit OS

## Project Preservation, Repair Strategy and Revised Development Plan

MOCK / DRAFT — pending_approval

My recommendation is to retain Proposal Guard as the main application, repair its existing decision and verification systems, and add a complete Bangladesh e-GP-specific feature set inside the same project.

We should not rebuild Proposal Guard from scratch, remove existing modules, or replace its architecture with a collection of independent AI agents.

The objective is to develop one integrated application that can discover e-GP opportunities, evaluate a company's tender eligibility, identify missing evidence, support bid preparation, and produce traceable, human-approved decisions.

### 1. Review of the attached development plan

The attached plan is directionally sound. Its strongest decision is to separate mandatory eligibility from strategic opportunity scoring. It also correctly prioritizes source freshness, evidence verification, and human approval over generating more AI features.

I recommend four modifications to that plan:

1. Make e-GP a dedicated feature domain, not a replacement for existing Proposal Guard functionality.
2. Treat Release 011 as a repair candidate, because your earlier terminal output confirms 34 passing tests twice, but does not yet establish that the patched files have been integrated into this attached project.
3. Move preservation and compatibility verification ahead of further changes. Every existing component, route, workflow, database record, report, and export must be accounted for.
4. Build complete e-GP functionality in stages, with manual official-document import available independently of automated tender discovery.

The attached plan identifies the relevant services and describes three previous safety failures. 

svgPasted markdown.md

### 2. The architecture we should preserve and extend

PROPOSAL GUARD

Existing application, components, workflows and data preserved

svg

svg

Existing core

Sources, documents, scoring, verification, workflow, reporting and export

svg

New e-GP domain

Tender intake, company profiles, qualifications, matching and bid readiness

svg

Shared evidence and approval controls

Source versions → Eligibility rules → Verification → Human approval → Controlled outputs

This is a proposed target architecture, not a claim that every displayed component is already implemented.

Archive inspection limitation: I have been able to review the attached Markdown plan and your Release 011 test logs, but the local archive inspection tool returned an error when attempting to open `Proposal Guard (2).zip`. Therefore, I cannot yet honestly certify a file-by-file audit of the ZIP, its complete dependency graph, or whether the patched services are present in that copy.

The technical recommendations below distinguish documented functionality from proposed additions.

## 3. Current components: preservation and repair matrix

Based on the service names in the plan and Release 011 logs, these are the primary areas to retain. File existence and exact behavior still need confirmation against the ZIP.

|   |
| - |

Existing component

|   |
| - |

Preservation decision

|   |
| - |

Required repair or extension

|   |
| - |

`bid_score_service.py`

|   |
| - |

Preserve

|   |
| - |

Separate mandatory eligibility and opportunity scoring

|   |
| - |

`verification_service.py`

|   |
| - |

Preserve

|   |
| - |

Require valid evidence; reject stale verification

|   |
| - |

`source_service.py`

|   |
| - |

Preserve

|   |
| - |

Add document versioning, hashing and amendment detection

|   |
| - |

`workflow_service.py`

|   |
| - |

Preserve

|   |
| - |

Enforce approval gates and freshness checks

|   |
| - |

`report_service.py`

|   |
| - |

Preserve

|   |
| - |

Generate e-GP-specific eligibility and gap reports

|   |
| - |

`export_service.py`

|   |
| - |

Preserve

|   |
| - |

Prevent unapproved reports from appearing client-ready

|   |
| - |

Existing UI/screens

|   |
| - |

Preserve

|   |
| - |

Add e-GP pages without removing current functionality

|   |
| - |

Existing data storage

|   |
| - |

Preserve

|   |
| - |

Add versioned e-GP data structures and safe migrations

|   |
| - |

Existing tests

|   |
| - |

Preserve

|   |
| - |

Add e-GP regression tests alongside existing tests

The plan should explicitly prohibit deleting or silently renaming existing modules, replacing API contracts, dropping database fields, or changing historical approvals.

### Release 011 assessment

Your supplied results show:

- Initial run: 34 tests passed.
- Independent rerun: 34 tests passed.
- Both runs exited successfully.
- Changes were prepared in a temporary development copy.

That is encouraging evidence for Stage 0 safety remediation, but it is not a complete integration certification.

Release 011 disposition: candidate for controlled integration, subject to source diff, compatibility, and full regression verification.

## 4. What a complete e-GP feature should contain

I recommend one integrated e-GP Tender Intelligence & Bid Readiness module, containing eight functional areas.

[About e-Government Procurement (e-GP) System](https://images.openai.com/static-rsc-4/wVEtxxUPneLhEnNPTRM0j6CuTcJIC1ZTAROohhhFdt9x-EHafrz8F9rlFujaSXWuJZ3V06-spdOYifmQJkMFpOAeTMOmWTZLgTRpXbhunMftmcM9WDLv9o3_85vF4M2tKDImfWGUMXifgoCdDP447z3im9uCuo80FOMJjjslwuc?purpose=inline)

01 — Official e-GP Tender Intake

Import tender ID, reference number, procuring entity, procurement method, published date, deadline, and official documents. Support manual import first, plus authorized automated retrieval when validated.

[Document management platform for ISO certification | Adexin](https://images.openai.com/static-rsc-4/Jg869DeYBzYqJV5LtR57SJDxTA-DVPhkkAGsYmxNl5ZUsolfZq_XWYE-CPuuXrDSH7BDJfryvvERSw3QKVMjcfL1JyhvThaVxiMTfw91WfKRIetTS_1u0b6dLNIK7N83xRicfafHh0GKJCSG-89NW2bhAS_wCy9fhAamAPFIioY?purpose=inline)

02 — Company Qualification Vault

Store company registration, financial capacity, historical turnover, similar work experience, personnel, equipment, bank facilities, certificates, and supporting records. Include expiry dates and evidence verification.

[eBrevia Contract Analyzer | AI-Powered Contract Review](https://images.openai.com/static-rsc-4/OXgYPGSVmLdDiL18F9CkDm1PDbFHJvZaeJSEnCt_zDEe4I0GTUA-MyWI6yGsAD9GA4HjVrKCmtVPw-UVLNEB7L9s2GVNjeNVmqxsvfnCjofcAxJbAYL-H_s2YNO211-n2RiNuSaX0ZpHHsvUbKgpFp7CRo8b-YFAZ0DyW02oLaM?purpose=inline)

03 — Tender Document & Clause Analyzer

Extract qualification requirements from uploaded e-GP documents. Every extracted rule needs its source, page or clause, value, unit, and confirmation status. AI suggestions must be reviewable.

[Fintech Fraud Prevention: Automate Financial Crime Effectiveness Testing with Cable](https://images.openai.com/static-rsc-4/9VF6JRs6q6d4qPS-PMy64CXrmE1iFNACO20uoDb7wTgUBCF451s47V6cbdE4gQcESheH_jnGiJH2vEbiWWT4LGXiaqqEIfN91tBi-xmT4ZSBQ4KSqH0tCpRBLhHtwCspWOSQYRAHCEtngoMjmVXnJFUvmy5lcbll9hYBC4NoLBw?purpose=inline)

04 — Deterministic Eligibility Engine

Compare tender requirements with the company's verified evidence. Separately assess mandatory criteria, missing documentation, and strategic attractiveness.

[How Construction Companies Can Win More Bids with TenderBot IO](https://images.openai.com/static-rsc-4/2KJa2JHKihWrj2X1UUkyu22xgrN8UdliMKjMdL4nv0_zy9n8TNwYYvCIa9oYV0MMKlKTQf-jqmrFRKkAtGU22PoNVminkrXcSYNxZOZp6ofUkzQ8kekDRFvTliUjJXD4ScbY31AJX74gRgLpgD55oGFozszSGKoqBy9uuLFE2Tc?purpose=inline)

05 — Tender-to-Fit Matching

Rank relevant tenders by eligibility, sector, location, capacity, time remaining, and commercial fit. A high score cannot override a failed qualification.

[Die Operations1 Software - Operations1 Software für Adaptive Process Execution](https://images.openai.com/static-rsc-4/kR5zfnvmgK8ahR83hTZ_yBEEu0X1tPp_Dgt1_vq9fxAzriV9O8U2AZgubIckeRHvjGEOYJEojNpmqu_oQgBssD8iPDSRV4BgzduO39uVUrOrkUrBeocAZ8rzQ__IahX1gqAj2AxNF6tx4tFjxOkMEe79xI2Bf3Dxg-ZgJboHkiw?purpose=inline)

06 — Bid Readiness Workspace

Track required forms, documentary evidence, technical requirements, financial attachments, clarifications, and responsible reviewers. Reuse existing tasks, workflow and verification services.

[Innova Compliance Chile: MPD Ley N° 20.393 | Innova Ibérica](https://images.openai.com/static-rsc-4/MUsyinSe2SuDQveQtHBXvQCkVsI1WByXgZ8Mh_XUW9-6z0Qzow9ZXmvDuSwILpk-6ptHTB00ePZbwoLtQEAsuMsd54lujvWhINssfFXBXefYOZuD4WDnUx9gq01_1hQ7Esz3A6U_joPcnfeGCN9c6H3gUv5n7ghXjWwdCOKZVzI?purpose=inline)

07 — Evidence-Based Reports and Exports

Produce eligibility matrices, risk reports, gap lists, deadline checklists, bid/no-bid assessments, and evidence inventories. Clearly label draft versus approved results.

[CAD Compliance Made Simple: Audit Trails Without the Headache | Reific](https://images.openai.com/static-rsc-4/ATNwbYuWGG3bcyoXRy0Ai7PJEYZyeDDEKCKQJhpYPRL_AHHLGl9IQ9Yui3ys6PKZKuRB2ALaNLaFoyN0gpIJM_yLy7PjkDUImw1sKQZt4R4LYRPBYub17GnoQGIKMPbUu_c0CLzHEz7m4Sv-UJzH8dVv7Y12Tf3iiOoiE6GGIag?purpose=inline)

08 — Amendment Monitoring and Approval Control

Monitor revised tender documents, addenda, deadline changes, and other relevant source updates. Trigger reassessment and invalidate dependent decisions when required.

These images illustrate the intended interface types; they are not screenshots of your current application.

### Official e-GP sources and regulatory boundaries

I checked the Bangladesh e-GP and BPPA websites. They support the feasibility of an e-GP-specific solution:

- Official advanced eTender/eProposal search includes tender identification, procurement categories, procuring entities and publication/closing-date filters. 

  [image](https://www.google.com/s2/favicons?domain=https://eprocure.gov.bd\&sz=32)

  e-GP

- Official eExperience search provides work-history-related fields relevant to qualification checks. 

  [image](https://www.google.com/s2/favicons?domain=https://eprocure.gov.bd\&sz=32)

  e-GP

- Official eContracts search exposes award and contract search information. 

  [image](https://www.google.com/s2/favicons?domain=https://eprocure.gov.bd\&sz=32)

  e-GP



Importantly, PPR 2025 became effective on September 28, 2025. Therefore, the new e-GP domain must be designed for current procurement rules and applicable tender-specific eSTDs, not hard-coded around older procurement assumptions. 

[image](https://www.google.com/s2/favicons?domain=https://www.bppa.gov.bd\&sz=32)

Bangladesh Public Procurement Authority

The public search pages do not themselves prove the existence of a supported programmatic API. Until permitted, reliable retrieval is established, manual upload and operator-assisted import should remain fully functional.

The new feature should support bid preparation and review inside Proposal Guard. It should not claim to submit bids directly to e-GP, automate credentials, bypass CAPTCHA, or perform authenticated portal actions without separately verified authorization and integration support.

## 5. Repair the decision engine before expanding it

The most important architectural change is a deterministic, evidence-governed eligibility engine.

Official e-GP tender + verified company profile

svg

Requirement-by-requirement evaluation

svg

svg

PASS

Fully verified

svg

FAIL

Mandatory gap

svg

UNKNOWN

Evidence missing

svg

Verification and human approval gate

Only fully verified, current decisions can receive positive bid clearance

Recommended precedence:

|   |
| - |

Eligibility

|   |
| - |

Recommendation

|   |
| - |

Workflow outcome

|   |
| - |

Verified PASS

|   |
| - |

PURSUE or REVIEW based on fit

|   |
| - |

Await human approval

|   |
| - |

Confirmed FAIL

|   |
| - |

DO_NOT_PURSUE

|   |
| - |

Positive clearance prohibited

|   |
| - |

UNKNOWN

|   |
| - |

REVIEW

|   |
| - |

Evidence blocker

|   |
| - |

Source amended

|   |
| - |

Reassessment required

|   |
| - |

Previous clearance invalid

|   |
| - |

Approval missing

|   |
| - |

No release clearance

|   |
| - |

Draft only

A source amendment should invalidate the affected checks and every decision that depends on them, while preserving earlier records for audit.

### Implementation details that matter

The engine needs to distinguish numeric comparisons, dates, document completeness, experience type, legal qualification, and tender-specific exceptions. `NOT_APPLICABLE` must require an explicit reason; it must never become an automatic pass.

For example, a BDT 3 crore minimum turnover requirement can be evaluated mathematically only when the correct accounting period, verified turnover figure, and applicable tender clause are known.

## 6. Revised implementation roadmap

The original six-stage plan should be reorganized into seven approval-gated releases. This avoids treating the entire e-GP system as one large, difficult-to-verify change.

|   |
| - |

Release

|   |
| - |

Priority

|   |
| - |

Deliverable

|   |
| - |

Verification gate

|   |
| - |

011A — Preservation

|   |
| - |

P0

|   |
| - |

Inventory, backups, Release 011 diff and baseline

|   |
| - |

Existing components and data preserved

|   |
| - |

012 — Safety Integration

|   |
| - |

P0

|   |
| - |

Mandatory blockers, source freshness, approval controls

|   |
| - |

Negative and regression tests pass

|   |
| - |

013 — e-GP Foundation

|   |
| - |

P1

|   |
| - |

Tender intake, identifiers, official sources, company profiles

|   |
| - |

Reliable manual import and provenance

|   |
| - |

014 — Eligibility Engine

|   |
| - |

P1

|   |
| - |

Clause matrix, evidence matching, deterministic qualification

|   |
| - |

No unsupported PASS

|   |
| - |

015 — Bid Readiness

|   |
| - |

P1

|   |
| - |

Gap analysis, matching, tasks, checklist, deadlines

|   |
| - |

End-to-end pilot passes

|   |
| - |

016 — Reporting & AI

|   |
| - |

P1

|   |
| - |

Evidence-based reports, optional AI extraction

|   |
| - |

Human benchmark and approval

|   |
| - |

017 — Source Automation

|   |
| - |

P2

|   |
| - |

Authorized e-GP monitoring, amendments, alerts

|   |
| - |

Reliability, compliance and freshness tests

The complete target feature set is Release 017; Releases 012–015 establish the essential usable e-GP workflow.

### Proposed extensions inside the current project

The exact directory layout must first be confirmed. Using the existing `tenderproof` service pattern as an architectural reference, I would add an isolated e-GP feature domain instead of redesigning the core:

```
tenderproof/
  services/
    bid_score_service.py        # Preserve + repair
    verification_service.py     # Preserve + repair
    source_service.py           # Preserve + extend
    workflow_service.py         # Preserve + verify
    report_service.py           # Preserve + extend
    export_service.py           # Preserve + extend

    egp/
      tender_intake_service.py
      tender_document_service.py
      company_profile_service.py
      qualification_service.py
      tender_matching_service.py
      bid_readiness_service.py
      amendment_service.py

tests/
  test_release_011.py
  test_egp_intake.py
  test_egp_eligibility.py
  test_egp_workflow.py
  test_egp_regression.py
```

These are proposed names, not confirmed existing paths. Actual package placement and API integration should follow the inspected repository's architecture.

## 7. Data preservation and integration requirements

The new e-GP domain should add records without destructively changing old ones.

Proposed additions include `EGPTender`, `EGPTenderDocument`, `CompanyQualificationProfile`, `EligibilityRequirement`, `EligibilityAssessment`, `EvidenceLink`, `TenderAmendment`, and `BidReadinessRecord`.

Each new record should have traceable relationships to the existing case, document, task, evidence, and verification models wherever equivalent records already exist. Avoid duplicating their responsibility.

For safety:

- Back up the complete project and persistent storage before applying changes.
- Use additive, versioned database migrations with rollback checks.
- Preserve original source documents and record SHA-256 hashes.
- Record assessment versions and the exact evidence snapshot used.
- Keep historical approvals, but prevent their reuse against changed source versions.
- Test report and export consumers after every model change.

These safeguards are particularly important because a successful test run in a temporary development copy does not verify the original project's database state.

## 8. Proposed end-to-end e-GP acceptance test

An example, using synthetic data:

Sample tender assessment

MOCK

Bangladesh e-GP works tender — illustrative criteria, not an actual tender.

|   |
| - |

Requirement

|   |
| - |

Minimum

|   |
| - |

Verified company

|   |
| - |

Result

|   |
| - |

Annual turnover

|   |
| - |

Tk 3 crore

|   |
| - |

Tk 5 crore

|   |
| - |

PASS

|   |
| - |

Similar experience

|   |
| - |

Tk 2 crore

|   |
| - |

Tk 1 crore

|   |
| - |

FAIL

|   |
| - |

Liquid assets

|   |
| - |

Tk 50 lakh

|   |
| - |

Not provided

|   |
| - |

UNKNOWN

|   |
| - |

Required certificate

|   |
| - |

Valid

|   |
| - |

Valid

|   |
| - |

PASS

Strategic attractiveness

# 91/100

Eligibility clearance

NOT ELIGIBLE

Expected result: `DO_NOT_PURSUE`

The system must explain the confirmed mandatory failure, separately identify missing evidence, prevent a positive bidding clearance, and create an auditable report.

The complete integration test should also verify that uploading an amended tender document triggers reassessment, that the earlier approval cannot authorize a new client-ready export, and that unrelated existing Proposal Guard cases remain unchanged.

## 9. Approval and next-action checklist

Proposed verification tasks

0 of 9 marked

Inventory all project files, modules, UI screens, dependencies and persistent data

Compare Release 011 patched files against the current project

Create and verify a restorable project and database backup

Integrate safety repairs without removing existing components

Run full tests and verify old UI and API workflows

Implement e-GP tender intake and company profile storage

Implement deterministic eligibility and source-linked evidence

Implement matching, bid readiness, reports and approval gates

Validate authorized official-source automation and pilot acceptance

svg Copy verification checklistCheckboxes are for planning and manual tracking; marking them does not verify that code changes or tests have been completed.

## Final recommendation

Keep the current Proposal Guard application intact and evolve it into Proposal Guard with a complete e-GP Tender-to-Fit module.

The next approval should cover Release 011A — Preservation and Integration Audit, not unrestricted implementation of all features.

The approval status remains `pending_approval`. Once the archive can be inspected and the preserved baseline is demonstrated, the next controlled deliverable should be a file-level implementation manifest identifying exactly which files to retain unchanged, repair, extend, or add—without sacrificing existing functionality.

This is the lowest-risk path toward a functional e-GP-specific system while preserving the investment already made in Proposal Guard.