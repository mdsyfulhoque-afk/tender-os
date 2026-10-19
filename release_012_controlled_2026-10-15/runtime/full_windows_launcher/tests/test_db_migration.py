import sqlite3

from sqlalchemy import inspect

from tenderproof.db import get_engine, init_db


def test_methodology_fields_are_added_without_erasing_existing_data(tmp_path):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE methodology_outline (id INTEGER PRIMARY KEY, case_id VARCHAR(80), module_title VARCHAR(255))")
        connection.execute("INSERT INTO methodology_outline (case_id, module_title) VALUES ('CASE-1', 'Existing module')")

    init_db(path)
    engine = get_engine(path)
    columns = {column["name"] for column in inspect(engine).get_columns("methodology_outline")}
    with engine.connect() as connection:
        row = connection.exec_driver_sql("SELECT case_id, module_title FROM methodology_outline").one()

    assert {"data_collection_conditions", "analysis_approach"}.issubset(columns)
    assert tuple(row) == ("CASE-1", "Existing module")
