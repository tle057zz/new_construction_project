"""Write issue measures from the SQL facts.

Counts totals by status, category, type, assignee, and company.
Also counts issues with a due date, issues with a location, and created-on months.
Does not modify the database. Does not calculate resolution time or overdue.
"""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "sql" / "snowdon_issues.sqlite"
REPORT = ROOT / "validation" / "measures.csv"

STATUS_ORDER = [
    "Open",
    "In dispute",
    "Draft",
    "Closed",
    "Completed",
    "In progress",
    "Pending",
    "Not approved",
    "In review",
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


def grouped(connection: sqlite3.Connection, sql: str) -> list[tuple[str, int]]:
    return [(label, count) for label, count in connection.execute(sql)]


def main() -> None:
    if not DATABASE.is_file():
        raise SystemExit(f"database not found: {DATABASE}")

    connection = sqlite3.connect(DATABASE)
    total = connection.execute("SELECT COUNT(*) FROM fact_issues").fetchone()[0]
    status = dict(grouped(
        connection,
        """
        SELECT status.status, COUNT(*)
        FROM fact_issues AS fact
        JOIN dim_status AS status ON status.status_id = fact.status_id
        GROUP BY status.status
        """,
    ))
    category = grouped(
        connection,
        """
        SELECT category.category, COUNT(*)
        FROM fact_issues AS fact
        JOIN dim_category AS category ON category.category_id = fact.category_id
        GROUP BY category.category
        ORDER BY COUNT(*) DESC, category.category
        """,
    )
    issue_type = grouped(
        connection,
        """
        SELECT type.type, COUNT(*)
        FROM fact_issues AS fact
        JOIN dim_type AS type ON type.type_id = fact.type_id
        GROUP BY type.type
        ORDER BY COUNT(*) DESC, type.type
        """,
    )
    assignee = grouped(
        connection,
        "SELECT assigned_to, COUNT(*) FROM fact_issues GROUP BY assigned_to ORDER BY COUNT(*) DESC, assigned_to",
    )
    company = grouped(
        connection,
        "SELECT company, COUNT(*) FROM fact_issues GROUP BY company ORDER BY COUNT(*) DESC, company",
    )
    with_due_date = connection.execute("SELECT COUNT(due_date) FROM fact_issues").fetchone()[0]
    with_location = connection.execute("SELECT COUNT(location) FROM fact_issues").fetchone()[0]
    created_month = grouped(
        connection,
        """
        SELECT strftime('%Y-%m', created_on), COUNT(*)
        FROM fact_issues
        GROUP BY 1
        ORDER BY 1
        """,
    )
    connection.close()

    rows = [("total", "issues", total)]
    rows.extend(("status", label, status[label]) for label in STATUS_ORDER)
    rows.extend(("category", label, count) for label, count in category)
    rows.extend(("type", label, count) for label, count in issue_type)
    rows.extend(("assignee", label, count) for label, count in assignee)
    rows.extend(("company", label, count) for label, count in company)
    rows.append(("with_due_date", "filled", with_due_date))
    rows.append(("with_location", "filled", with_location))
    rows.extend(("created_month", label, count) for label, count in created_month)

    type_counts = dict(issue_type)
    month_total = sum(count for _label, count in created_month)
    if (
        total != 289
        or status != EXPECTED_STATUS
        or sum(count for _label, count in category) != 289
        or len(category) != 18
        or category[0] != ("Safety", 72)
        or sum(count for _label, count in issue_type) != 289
        or len(issue_type) != 33
        or type_counts.get("RFI") != 3
        or assignee != [("Autodesk", 289)]
        or company != [("Autodesk", 289)]
        or with_due_date != 242
        or with_location != 81
        or month_total != 289
        or any(name in {"resolution_time", "overdue"} for name, _label, _count in rows)
    ):
        raise SystemExit("measure check failed")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["measure", "label", "rows"])
        writer.writerows(rows)

    recorded_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"recorded_at: {recorded_at}")
    print(f"total: {total}")
    print(f"with_due_date: {with_due_date}")
    print(f"with_location: {with_location}")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
