import os
import json
import tempfile
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "tenders"
UPLOAD_DIR = BASE_DIR / "uploads"

OCR_CHAR_THRESHOLD = 40
MAX_CHUNK_TOKENS = 1200

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def atomic_write_json(filepath: Path, data):
    """Safely writes JSON to disk using atomic temp file replacement."""
    dir_path = filepath.parent
    os.makedirs(dir_path, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
        os.replace(tmp_path, filepath)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise