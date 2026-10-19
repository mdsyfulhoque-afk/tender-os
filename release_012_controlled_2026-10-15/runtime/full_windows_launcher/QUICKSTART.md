# TenderProof OS Quickstart

## Fastest Start

1. Double-click `deploy&run.bat`.
2. Wait for dependencies, database initialization, tests, and Streamlit launch.
3. Open `http://localhost:8501` if the browser does not open automatically.
4. Click `Create demo case` on the Home page.

## Manual Command Line

```bash
cd tenderproof_os
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python run_app.py --check
python run_app.py --run
```

## Create First Real Diagnostic

1. `Create or Open Case`: create client/tender record.
2. `Upload / Register Inputs`: upload PDF/DOCX/TXT or paste ToR text.
3. `ToR Extraction`: create normalized requirements.
4. `Compliance Matrix`: auto-create compliance rows and add evidence.
5. `CV Matcher`: add expert/candidate evidence.
6. `Bid/No-Bid Scorecard`: score all 10 categories and generate recommendation.
7. `Risk Register and Gaps`: sync gaps and auto-generate risks.
8. `Proposal Skeleton and Methodology`: add sections/modules.
9. `Diagnostic Report Generator`: generate Markdown and DOCX reports.
10. `Excel Export`: generate workbook.
11. `Verification / Audit Log`: run readiness checks.

## Report

Reports are saved in:

```text
storage\reports
```

## Excel Workbook

Exports are saved in:

```text
storage\exports
```

## Reset / Demo

Use `Settings` to initialize folders/database, refresh seed CSVs, or create another demo case.

