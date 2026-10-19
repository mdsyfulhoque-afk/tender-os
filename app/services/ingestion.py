import hashlib
import uuid
from pathlib import Path
from app.config import DATA_DIR, atomic_write_json

def compute_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ingest_files(files: list) -> str:
    tender_id = str(uuid.uuid4())
    tender_dir = DATA_DIR / tender_id
    tender_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "tender_id": tender_id,
        "files": []
    }
    
    for f in files:
        filename = f.filename
        save_path = tender_dir / filename
        f.save(str(save_path))
        
        sha = compute_sha256(str(save_path))
        manifest["files"].append({
            "filename": filename,
            "path": str(save_path),
            "sha256": sha
        })
        
    manifest_path = tender_dir / "tender_manifest.json"
    atomic_write_json(manifest_path, manifest)
        
    return tender_id