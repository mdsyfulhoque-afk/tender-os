import argparse
import subprocess
import sys
import socket
import sqlite3

from tenderproof.config import PROJECT_ROOT, ensure_directories
from tenderproof.db import get_db_path, get_session, init_db
from tenderproof.services.sample_data_service import create_demo_case, create_seed_csvs


def init_database() -> None:
    ensure_directories()
    path = init_db()
    create_seed_csvs()
    print(f"Database initialized: {path}")


def seed_demo() -> None:
    init_database()
    with get_session() as session:
        case = create_demo_case(session)
        print(f"Demo case created: {case.case_id}")


def check() -> int:
    imports = [
        "streamlit",
        "sqlalchemy",
        "pandas",
        "openpyxl",
        "docx",
        "pypdf",
        "pytest",
    ]
    for package in imports:
        __import__(package)
    path = get_db_path().resolve()
    if path.is_file():
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("Database integrity check failed.")
    print("TenderProof OS check passed.")
    return 0


def run(port: int = 8501) -> int:
    if not 1024 <= port <= 65515:
        raise ValueError("Choose a preferred port between 1024 and 65515.")
    init_database()
    for selected_port in range(port, port + 20):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", selected_port))
                break
            except OSError:
                continue
    else:
        raise RuntimeError("No available local port near the requested port.")
    print("Starting TenderProof OS...")
    print(f"App URL: http://localhost:{selected_port}")
    return subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(selected_port), "--server.address", "localhost"], cwd=PROJECT_ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="TenderProof OS local launcher")
    parser.add_argument("--init-db", action="store_true", help="Initialize SQLite database and folders.")
    parser.add_argument("--seed-demo", action="store_true", help="Create a demo diagnostic case.")
    parser.add_argument("--check", action="store_true", help="Run import and database checks.")
    parser.add_argument("--run", action="store_true", help="Launch Streamlit app.")
    parser.add_argument("--port", type=int, default=8501, help="Preferred local port.")
    args = parser.parse_args()

    if args.seed_demo:
        seed_demo()
        return 0
    if args.check:
        return check()
    if args.init_db:
        init_database()
        return 0
    if args.run or not (args.seed_demo or args.check or args.init_db):
        return run(args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

