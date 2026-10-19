import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(os.environ.get("TENDERPROOF_RUNTIME_ROOT", str(PROJECT_ROOT))).resolve()
DATA_DIR = RUNTIME_ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
REFERENCE_DIR = DATA_DIR / "reference"
STORAGE_DIR = RUNTIME_ROOT / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
EXTRACTED_TEXT_DIR = STORAGE_DIR / "extracted_text"
REPORTS_DIR = STORAGE_DIR / "reports"
EXPORTS_DIR = STORAGE_DIR / "exports"
BACKUPS_DIR = STORAGE_DIR / "backups"
EVIDENCE_DIR = STORAGE_DIR / "evidence"
DB_PATH = STORAGE_DIR / "tenderproof.db"

REQUIRED_DIRS = [
    DATA_DIR,
    SEED_DIR,
    REFERENCE_DIR,
    STORAGE_DIR,
    UPLOADS_DIR,
    EXTRACTED_TEXT_DIR,
    REPORTS_DIR,
    EXPORTS_DIR,
    BACKUPS_DIR,
    EVIDENCE_DIR,
]


def ensure_directories() -> None:
    for directory in REQUIRED_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)

