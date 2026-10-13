"""Export the SQL facts and lookups to the Power BI CSV files.

Reads sql/snowdon_issues.sqlite only. Does not modify the database.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "sql" / "snowdon_issues.sqlite"
OUT = ROOT / "powerbi"

EXPORTS = {
    "dim_status.csv": "SELECT status_id, status FROM dim_status ORDER BY status_id",
    "dim_category.csv": "SELECT category_id, category FROM dim_category ORDER BY category_id",
    "dim_type.csv": "SELECT type_id, type FROM dim_type ORDER BY type_id",
    "fact_issues.csv": """
        SELECT id, title, status_id, category_id, type_id, assigned_to, company,
               created_on, substr(created_on, 1, 7) AS created_month,
               due_date, start_date, updated_on, closed_at, location, published,
               source_file, source_sheet, ingestion_timestamp
        FROM fact_issues
        ORDER BY CAST(substr(id, 2) AS INTEGER) DESC
    """,
}


def main() -> None:
    if not DATABASE.is_file():
        raise SystemExit(f"database not found: {DATABASE}")
    OUT.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    for name, sql in EXPORTS.items():
        rows = connection.execute(sql).fetchall()
        path = OUT / name
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(rows[0].keys())
            for row in rows:
                writer.writerow(["" if value is None else value for value in row])
        print(f"wrote {path} rows={len(rows)}")
    connection.close()


if __name__ == "__main__":
    main()
