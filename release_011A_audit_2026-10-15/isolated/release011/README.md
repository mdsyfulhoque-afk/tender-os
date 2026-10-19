# TenderProof OS / ProposalGuard

TenderProof OS / ProposalGuard is a local-first internal MVP for running a cash-first donor tender/proposal diagnostic workflow.

It helps Syful intake donor ToRs, normalize requirements, build compliance matrices, map CV evidence, identify gaps and risks, score bid/no-bid decisions, generate diagnostic reports, export Excel workbooks, and capture reusable proposal intelligence/IP.

This is not a public SaaS. It has no billing, no multi-tenant auth, and no marketplace. It is a local operating system for paid TenderProof Rapid Bid Diagnostic delivery.

## What It Does

- Create and manage diagnostic cases
- Upload or paste ToR/source text; scanned PDFs use optional local OCR when dependencies are installed
- Large scanned PDFs show page-by-page OCR progress, up to 200 pages per file; OCR text must be human-checked
- Extract text from TXT, DOCX, and PDF files
- Normalize ToR clauses into atomic requirements
- Generate stable `match_key` and `canonical_anchor` values
- Auto-create compliance rows
- Create GapItems from missing evidence or Pending Input rows
- Add CV/expert matching evidence without inventing claims
- Score bid/no-bid readiness across 10 required categories
- Generate Markdown and DOCX diagnostic reports
- Export a 15-sheet Excel diagnostic workbook
- Run verification checks and readiness labeling
- Capture reusable donor/sector/proposal IP
- Optimize the case workflow with next-step guidance
- Track Bangladesh e-GP registration, tender preparation/submission, and post-award readiness
- Record data-collection conditions and the planned human-led, rules-based NLP, or SLM-assisted analysis approach

## Run With Double Click

Open:

```text
deploy&run.bat
```

If the ampersand causes trouble in your shell or shortcut, use:

```text
deploy_and_run.bat
```

Both launchers create a virtual environment, install requirements, initialize the database, run tests, and start Streamlit.

App URL:

```text
http://localhost:8501
```

## Run With Python

```bash
python run_app.py --init-db
python run_app.py --seed-demo
python run_app.py --check
python run_app.py --run
```

## First Diagnostic Case

1. Open `Create or Open Case`.
2. Create a new case with client, tender, donor, country, sector, and deadline details.
3. Go to `Upload / Register Inputs`.
4. Upload a ToR file or paste manual ToR text.
5. Go to `ToR Extraction` and create requirements from the source.
6. Go to `Compliance Matrix` and auto-create compliance rows.
7. Enter available evidence, mark gaps, and sync GapItems.
8. Add CV evidence in `CV Matcher`.
9. Score the tender in `Bid/No-Bid Scorecard`.
10. Add proposal skeleton and methodology modules.
11. Generate reports and Excel export.
12. Run verification before using client-ready outputs.

## Output Locations

- Uploaded files: `storage/uploads`
- Extracted text: `storage/extracted_text`
- Reports: `storage/reports`
- Excel exports: `storage/exports`
- SQLite database: `storage/tenderproof.db`

## Safety Rules

- The app does not guarantee tender wins.
- Missing evidence is marked as Gap or Pending Input.
- CV suggestions use provided evidence only.
- Verification flags prohibited report language before export-ready status.

## Known v0.1 Limits

- No external AI API is connected yet; prompt files are included for assisted workflows.
- SLM-assisted is a planning label only; no language model/provider is connected. OCR runs locally through RapidOCR when installed and should always be checked against the source. Bangladesh e-GP notes and the supplied guide's OCR transcript are under `tenderproof/reference` and `data/reference`.
- Authentication and multi-client SaaS concerns are intentionally out of scope.

