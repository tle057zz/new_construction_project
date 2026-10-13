"""Reconcile the issue workbook through the SQL facts.

Compares the raw workbook, staged rows, curated rows, and SQLite tables.
Checks row counts, unique IDs, status counts, and lookup joins.
Does not modify those sources. Does not calculate resolution time or overdue.
"""

from __future__ import annotations

import csv
import sqlite3
from collections import Counter
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from ingest_issues import RAW, sheet_rows

ROOT = Path(__file__).resolve().parents[1]
STAGED = ROOT / "data" / "staged" / "issues.csv"
CURATED = ROOT / "data" / "curated" / "issues.csv"
DATABASE = ROOT / "sql" / "snowdon_issues.sqlite"
REPORT = ROOT / "validation" / "reconcile.csv"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

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
BLANK_FIELDS = {
    "description": 157,
    "location": 208,
    "root_cause": 171,
    "due_date": 47,
    "closed_at": 275,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def workbook_rows() -> list[dict[str, str]]:
    book = ZipFile(RAW)
    strings_root = ET.fromstring(book.read("xl/sharedStrings.xml"))
    strings = [
        "".join((node.text or "") for node in item.findall(".//m:t", NS))
        for item in strings_root.findall("m:si", NS)
    ]
    parsed = sheet_rows(book, "xl/worksheets/sheet2.xml", strings)
    header = [value for value, _kind in parsed[0]]
    rows = []
    for cells in parsed[1:]:
        rows.append({header[index]: cells[index][0].strip() for index in range(len(header))})
    return rows


def add(checks: list[dict[str, str]], name: str, expected: str, actual: str) -> None:
    checks.append({
        "check": name,
        "expected": expected,
        "actual": actual,
        "result": "pass" if expected == actual else "fail",
    })


def blank_count(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if not (row.get(field) or "").strip())


def main() -> None:
    for path in (RAW, STAGED, CURATED, DATABASE):
        if not path.exists():
            raise SystemExit(f"missing source: {path}")

    workbook = workbook_rows()
    staged = read_csv(STAGED)
    curated = read_csv(CURATED)
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    facts = list(connection.execute(
        """
        SELECT
            fact.id, status.status, category.category, type.type,
            fact.created_on, fact.due_date, fact.closed_at, fact.location
        FROM fact_issues AS fact
        JOIN dim_status AS status ON status.status_id = fact.status_id
        JOIN dim_category AS category ON category.category_id = fact.category_id
        JOIN dim_type AS type ON type.type_id = fact.type_id
        """
    ))
    issue_row_count = connection.execute("SELECT COUNT(*) FROM issue_rows").fetchone()[0]
    sql_blanks = {
        field: connection.execute(
            f"SELECT COUNT(*) FROM issue_rows WHERE {field} IS NULL"
        ).fetchone()[0]
        for field in BLANK_FIELDS
    }
    connection.close()

    layers = {
        "workbook": workbook,
        "staged": staged,
        "curated": curated,
    }
    checks: list[dict[str, str]] = []
    add(checks, "workbook_rows", "289", str(len(workbook)))
    add(checks, "staged_rows", "289", str(len(staged)))
    add(checks, "curated_rows", "289", str(len(curated)))
    add(checks, "issue_rows", "289", str(issue_row_count))
    add(checks, "fact_join_rows", "289", str(len(facts)))

    id_sets = {
        name: {row["id"] if name != "workbook" else row["ID"] for row in rows}
        for name, rows in layers.items()
    }
    id_sets["facts"] = {row["id"] for row in facts}
    for name, ids in id_sets.items():
        add(checks, f"{name}_unique_ids", "289", str(len(ids)))
    add(checks, "ids_match_across_layers", "yes", "yes" if len({frozenset(ids) for ids in id_sets.values()}) == 1 else "no")

    curated_by_id = {row["id"]: row for row in curated}
    staged_by_id = {row["id"]: row for row in staged}
    workbook_by_id = {row["ID"]: row for row in workbook}
    status_mismatches = 0
    label_mismatches = 0
    for fact in facts:
        source = workbook_by_id[fact["id"]]
        staged_row = staged_by_id[fact["id"]]
        curated_row = curated_by_id[fact["id"]]
        if not (source["Status"] == staged_row["status"] == curated_row["status"] == fact["status"]):
            status_mismatches += 1
        if not (
            source["Category"] == curated_row["category"] == fact["category"]
            and source["Type"] == curated_row["type"] == fact["type"]
        ):
            label_mismatches += 1
    add(checks, "status_mismatches", "0", str(status_mismatches))
    add(checks, "category_type_mismatches", "0", str(label_mismatches))

    fact_status = Counter(row["status"] for row in facts)
    for label, expected in EXPECTED_STATUS.items():
        add(checks, f"status_{label}", str(expected), str(fact_status[label]))
    add(checks, "status_total", "289", str(sum(fact_status.values())))

    for field, expected in BLANK_FIELDS.items():
        add(checks, f"curated_blank_{field}", str(expected), str(blank_count(curated, field)))
        add(checks, f"sql_blank_{field}", str(expected), str(sql_blanks[field]))

    sample = curated_by_id["#1873"]
    add(checks, "sample_1873_created_on", "2026-08-03T16:55:53", sample["created_on"])
    add(checks, "sample_1873_staged_serial", "46237.705474537041", staged_by_id["#1873"]["created_on"])

    failed = [row for row in checks if row["result"] == "fail"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "expected", "actual", "result"])
        writer.writeheader()
        writer.writerows(checks)

    recorded_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"recorded_at: {recorded_at}")
    print(f"checks: {len(checks)}")
    print(f"passed: {len(checks) - len(failed)}")
    print(f"failed: {len(failed)}")
    print(f"wrote {REPORT}")
    if failed:
        raise SystemExit("reconcile failed")


if __name__ == "__main__":
    main()
