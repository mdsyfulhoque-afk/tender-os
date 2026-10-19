import argparse
import subprocess
import sys

from tenderproof.config import PROJECT_ROOT, ensure_directories
from tenderproof.db import get_session, init_db
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
    init_database()
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
    print("TenderProof OS check passed.")
    return 0


def run() -> int:
    init_database()
    print("Starting TenderProof OS...")
    print("App URL: http://localhost:8501")
    return subprocess.call([sys.executable, "-m", "streamlit", "run", "app.py"], cwd=PROJECT_ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="TenderProof OS local launcher")
    parser.add_argument("--init-db", action="store_true", help="Initialize SQLite database and folders.")
    parser.add_argument("--seed-demo", action="store_true", help="Create a demo diagnostic case.")
    parser.add_argument("--check", action="store_true", help="Run import and database checks.")
    parser.add_argument("--run", action="store_true", help="Launch Streamlit app.")
    args = parser.parse_args()

    if args.seed_demo:
        seed_demo()
        return 0
    if args.check:
        return check()
    if args.init_db:
        init_database()
        return 0
    if args.run or not any(vars(args).values()):
        return run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

