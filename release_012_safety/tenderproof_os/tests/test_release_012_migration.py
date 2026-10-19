import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

import run_app
from tenderproof.db import init_db
from tenderproof import migrations


def table_hashes(connection):
    tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    result = {}
    for name in tables:
        columns = [r[1] for r in connection.execute(f'PRAGMA table_info("{name}")')]
        rows = connection.execute(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall()
        result[name] = {"columns": columns, "count": len(rows), "digest": hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()}
    return result


def test_migration_preserves_all_existing_columns_and_values(tmp_path):
    original = Path(__file__).resolve().parents[1] / "storage" / "tenderproof.db"
    target = tmp_path / "restored.db"
    source_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    with sqlite3.connect(original.as_uri() + "?mode=ro", uri=True) as source, sqlite3.connect(target) as destination:
        source.backup(destination)
        before = table_hashes(destination)
    init_db(target)
    init_db(target)
    with sqlite3.connect(target) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        for name, info in before.items():
            columns = ','.join('"' + c + '"' for c in info["columns"])
            rows = connection.execute(f'SELECT {columns} FROM "{name}" ORDER BY rowid').fetchall()
            assert len(rows) == info["count"]
            assert hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest() == info["digest"], name
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations WHERE version=?", (migrations.VERSION,)).fetchone()[0] == 1
    assert hashlib.sha256(original.read_bytes()).hexdigest() == source_hash
    assert list((tmp_path / "backups").glob("*.db"))


def test_failed_migration_rolls_back_ddl_and_data(tmp_path, monkeypatch):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE methodology_outline (id INTEGER PRIMARY KEY, case_id TEXT, module_title TEXT)")
        connection.execute("INSERT INTO methodology_outline VALUES (1, 'UNCHANGED', 'Original')")
    original_apply = migrations._apply_columns

    def fail_after_ddl(connection):
        original_apply(connection)
        raise RuntimeError("Injected migration failure")

    monkeypatch.setattr(migrations, "_apply_columns", fail_after_ddl)
    with pytest.raises(RuntimeError, match="Injected"):
        init_db(path)
    with sqlite3.connect(path) as connection:
        assert [r[1] for r in connection.execute("PRAGMA table_info(methodology_outline)")] == ["id", "case_id", "module_title"]
        assert connection.execute("SELECT * FROM methodology_outline").fetchone() == (1, "UNCHANGED", "Original")
        assert connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0] == 1


def test_check_is_read_only_for_database(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE keep_me (value TEXT)")
        connection.execute("INSERT INTO keep_me VALUES ('Original')")
    before = path.read_bytes()
    monkeypatch.setenv("TENDERPROOF_DB_PATH", str(path))
    assert run_app.check() == 0
    assert path.read_bytes() == before


def test_default_launcher_invocation_still_runs(monkeypatch):
    monkeypatch.setattr(run_app.sys, "argv", ["run_app.py"])
    monkeypatch.setattr(run_app, "run", lambda port: port)
    assert run_app.main() == 8501
