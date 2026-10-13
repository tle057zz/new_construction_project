"""Load the curated issue files into SQLite.

Reads the curated CSV files and sql/01_issues.sql.
Replaces sql/snowdon_issues.sqlite on each run.
Does not modify the raw workbook, the staged files, or the curated files.
Does not calculate resolution time or overdue.
"""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURATED_OVERVIEW = ROOT / "data" / "curated" / "overview.csv"
CURATED_ISSUES = ROOT / "data" / "curated" / "issues.csv"
SQL_FILE = ROOT / "sql" / "01_issues.sql"
DATABASE = ROOT / "sql" / "snowdon_issues.sqlite"

ISSUE_COLUMNS = [
    "id", "title", "status", "category", "type", "description", "assigned_to",
    "company", "watchers", "created_by", "created_on", "due_date", "start_date",
    "location", "location_details", "placement", "root_cause", "published",
    "updated_by", "updated_on", "closed_by", "closed_at", "comments",
    "additional_comments", "areas_affected", "building_element", "cost_impact",
    "date_received", "defect", "linked_asset", "facilities_team_review_status",
    "hyperlink_1", "hyperlink_2", "install_date", "interface_topic",
    "lessons_learned_candidate", "multi_select_dropdown", "numeric_field",
    "part_number", "project_task_code", "quality_issue_with_cost",
    "review_status", "risk_level", "row_label", "sc_acknowledged", "seat",
    "serial_number_1", "serial_number_2", "ship_date", "size_text",
    "warranty_info", "warranty_number", "work_order_number", "source_file",
    "source_sheet", "ingestion_timestamp",
]

EXPECTED_STATUS = {
    "Open": 148,
    "In dispute": 51,
    "Draft": 46,
    "Closed": 11,
    "Completed": 11,
    "In progress": 7,
    "Pending": 7,
    "Not approved": 5,
    "In review": 3,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    return text or None


def main() -> None:
    if not CURATED_ISSUES.is_file() or not CURATED_OVERVIEW.is_file():
        raise SystemExit("curated files not found; clean has to be run first")
    if not SQL_FILE.is_file():
        raise SystemExit(f"sql file not found: {SQL_FILE}")

    overview = read_csv(CURATED_OVERVIEW)
    issues = read_csv(CURATED_ISSUES)
    if list(issues[0]) != ISSUE_COLUMNS:
        raise SystemExit("curated issue columns do not match the SQL load")

    if DATABASE.exists():
        DATABASE.unlink()
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SQL_FILE.read_text(encoding="utf-8"))

    connection.executemany(
        """
        INSERT INTO overview (
            excel_cell, value, value_kind, source_file, source_sheet, ingestion_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["excel_cell"],
                blank_to_none(row["value"]),
                row["value_kind"],
                row["source_file"],
                row["source_sheet"],
                row["ingestion_timestamp"],
            )
            for row in overview
        ],
    )
    connection.executemany(
        f"INSERT INTO issue_rows ({', '.join(ISSUE_COLUMNS)}) VALUES ({', '.join('?' for _ in ISSUE_COLUMNS)})",
        [tuple(blank_to_none(row[name]) for name in ISSUE_COLUMNS) for row in issues],
    )

    connection.execute(
        "INSERT INTO dim_status (status) SELECT DISTINCT status FROM issue_rows ORDER BY status"
    )
    connection.execute(
        "INSERT INTO dim_category (category) SELECT DISTINCT category FROM issue_rows ORDER BY category"
    )
    connection.execute(
        "INSERT INTO dim_type (type) SELECT DISTINCT type FROM issue_rows ORDER BY type"
    )
    connection.execute(
        """
        INSERT INTO fact_issues (
            id, title, status_id, category_id, type_id, assigned_to, company,
            created_on, due_date, start_date, updated_on, closed_at, location,
            published, source_file, source_sheet, ingestion_timestamp
        )
        SELECT
            rows.id, rows.title, status.status_id, category.category_id, type.type_id,
            rows.assigned_to, rows.company, rows.created_on, rows.due_date,
            rows.start_date, rows.updated_on, rows.closed_at, rows.location,
            rows.published, rows.source_file, rows.source_sheet, rows.ingestion_timestamp
        FROM issue_rows AS rows
        JOIN dim_status AS status ON status.status = rows.status
        JOIN dim_category AS category ON category.category = rows.category
        JOIN dim_type AS type ON type.type = rows.type
        """
    )
    connection.commit()

    def count(sql: str) -> int:
        return connection.execute(sql).fetchone()[0]

    status_counts = dict(connection.execute(
        """
        SELECT status.status, COUNT(*)
        FROM fact_issues AS fact
        JOIN dim_status AS status ON status.status_id = fact.status_id
        GROUP BY status.status
        """
    ))
    checks = {
        "overview": count("SELECT COUNT(*) FROM overview"),
        "issue_rows": count("SELECT COUNT(*) FROM issue_rows"),
        "fact_issues": count("SELECT COUNT(*) FROM fact_issues"),
        "unique_ids": count("SELECT COUNT(DISTINCT id) FROM fact_issues"),
        "dim_status": count("SELECT COUNT(*) FROM dim_status"),
        "dim_category": count("SELECT COUNT(*) FROM dim_category"),
        "dim_type": count("SELECT COUNT(*) FROM dim_type"),
        "join_status": count(
            "SELECT COUNT(*) FROM fact_issues JOIN dim_status USING (status_id)"
        ),
        "join_category": count(
            "SELECT COUNT(*) FROM fact_issues JOIN dim_category USING (category_id)"
        ),
        "join_type": count(
            "SELECT COUNT(*) FROM fact_issues JOIN dim_type USING (type_id)"
        ),
        "due_date": count("SELECT COUNT(due_date) FROM fact_issues"),
        "closed_at": count("SELECT COUNT(closed_at) FROM fact_issues"),
    }
    tables = [name for (name,) in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    )]
    connection.close()

    expected = {
        "overview": 10,
        "issue_rows": 289,
        "fact_issues": 289,
        "unique_ids": 289,
        "dim_status": 9,
        "dim_category": 18,
        "dim_type": 33,
        "join_status": 289,
        "join_category": 289,
        "join_type": 289,
        "due_date": 242,
        "closed_at": 14,
    }
    if checks != expected or status_counts != EXPECTED_STATUS or tables != [
        "dim_category", "dim_status", "dim_type", "fact_issues", "issue_rows", "overview"
    ]:
        raise SystemExit(f"sql check failed: {checks} status={status_counts} tables={tables}")

    recorded_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"recorded_at: {recorded_at}")
    print(f"database: {DATABASE}")
    print(f"tables: {', '.join(tables)}")
    for name, value in checks.items():
        print(f"{name}: {value}")
    print("resolution_time: not calculated")
    print("overdue: not calculated")


if __name__ == "__main__":
    main()
