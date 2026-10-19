"""Transactional additive migrations; existing rows and artifacts are retained."""

from datetime import UTC, datetime
from pathlib import Path
import sqlite3
from uuid import uuid4

from sqlalchemy import inspect

VERSION = "012_safety_1"
COLUMNS = {
    "cases": {"assessment_revision": "INTEGER DEFAULT 0"},
    "sources": {
        "content_sha256": "VARCHAR(64)", "text_sha256": "VARCHAR(64)",
        "version_number": "INTEGER DEFAULT 1", "supersedes_source_id": "VARCHAR(80)",
        "reviewed_sha256": "VARCHAR(64)", "reviewed_text_sha256": "VARCHAR(64)",
        "reviewed_by": "VARCHAR(255)", "reviewed_at": "DATETIME", "review_notes": "TEXT",
        "requirements_complete": "BOOLEAN DEFAULT 0",
    },
    "verification_results": {"run_id": "VARCHAR(80)"},
    "output_packages": {"snapshot_hash": "VARCHAR(64)", "approval_id": "VARCHAR(80)", "verification_run_id": "VARCHAR(80)", "content_sha256": "VARCHAR(64)"},
    "methodology_outline": {"data_collection_conditions": "TEXT", "analysis_approach": "VARCHAR(120)"},
}


def _apply_columns(connection):
    for table, fields in COLUMNS.items():
        existing = {c["name"] for c in inspect(connection).get_columns(table)}
        for name, sql_type in fields.items():
            if name not in existing:
                connection.exec_driver_sql(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {sql_type}')


def migrate(engine, db_path: Path, metadata):
    with engine.connect() as connection:
        if "schema_migrations" in inspect(connection).get_table_names():
            if connection.exec_driver_sql("SELECT 1 FROM schema_migrations WHERE version=?", (VERSION,)).first():
                return
    if db_path.is_file() and db_path.stat().st_size:
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{db_path.stem}_pre_012_{uuid4().hex[:10]}.db"
        with sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(backup_path) as target:
            source.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Pre-migration database backup failed integrity check.")
    with engine.connect() as connection:
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        try:
            metadata.create_all(connection)
            _apply_columns(connection)
            connection.exec_driver_sql("INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)", (VERSION, datetime.now(UTC).isoformat()))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
