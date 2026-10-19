import sys
import os
import tempfile
from pathlib import Path

import pytest

_runtime = tempfile.TemporaryDirectory(prefix="tenderproof_test_runtime_")
os.environ["TENDERPROOF_RUNTIME_ROOT"] = _runtime.name

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tenderproof.db import Base, get_engine, make_session  # noqa: E402
from tenderproof import models  # noqa: F401,E402


@pytest.fixture()
def session(tmp_path):
    db_path = tmp_path / "test.db"
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    SessionLocal = make_session(db_path)
    session = SessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()
        engine.dispose()

