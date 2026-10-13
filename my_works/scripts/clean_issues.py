"""Clean staged issue rows into the curated layer.

Reads the staged CSV files only. Does not modify the raw workbook or the staged files.
Converts Excel date serials to timestamps. Blank text stays blank.
Does not calculate resolution time or overdue.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGED_OVERVIEW = ROOT / "data" / "staged" / "overview.csv"
STAGED_ISSUES = ROOT / "data" / "staged" / "issues.csv"
CURATED = ROOT / "data" / "curated"
OVERVIEW_OUT = CURATED / "overview.csv"
ISSUES_OUT = CURATED / "issues.csv"

DATE_COLUMNS = {
    "created_on": 289,
    "updated_on": 289,
    "due_date": 242,
    "start_date": 104,
    "closed_at": 14,
}
EXCEL_EPOCH = datetime(1899, 12, 30)


def excel_serial_to_timestamp(text: str) -> str:
    value = Decimal(text)
    days = int(value)
    seconds = ((value - Decimal(days)) * Decimal(86400)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if seconds == 86400:
        days += 1
        seconds = Decimal(0)
    stamp = EXCEL_EPOCH + timedelta(days=days, seconds=int(seconds))
    if stamp.year < 1990 or stamp.year > 2100:
        raise ValueError(f"serial {text} is outside 1990–2100")
    return stamp.isoformat(timespec="seconds")


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SystemExit(f"missing header: {path}")
        return list(reader.fieldnames), list(reader)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not STAGED_ISSUES.is_file() or not STAGED_OVERVIEW.is_file():
        raise SystemExit("staged files not found; ingest has to be run first")

    overview_fields, overview = read_csv(STAGED_OVERVIEW)
    issue_fields, issues = read_csv(STAGED_ISSUES)
    missing = [name for name in DATE_COLUMNS if name not in issue_fields]
    if missing:
        raise SystemExit(f"staged issues are missing date columns: {', '.join(missing)}")

    cleaned_overview = [
        {name: (row.get(name) or "").strip() for name in overview_fields}
        for row in overview
    ]

    cleaned = []
    converted = Counter()
    for row in issues:
        record = {}
        for name in issue_fields:
            value = (row.get(name) or "").strip()
            if name in DATE_COLUMNS and value:
                value = excel_serial_to_timestamp(value)
                converted[name] += 1
            record[name] = value
        cleaned.append(record)

    ids = [row["id"] for row in cleaned]
    blank_ids = sum(1 for item in ids if not item)
    duplicate_ids = sum(count - 1 for count in Counter(ids).values() if count > 1)
    status_counts = Counter(row["status"] for row in cleaned)
    expected_status = {
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
    if (
        len(cleaned) != 289
        or len(set(ids)) != 289
        or blank_ids
        or duplicate_ids
        or len(cleaned_overview) != 10
        or dict(converted) != DATE_COLUMNS
        or dict(status_counts) != expected_status
    ):
        raise SystemExit(
            f"clean check failed: issues={len(cleaned)} overview={len(cleaned_overview)} "
            f"unique={len(set(ids))} blank_ids={blank_ids} duplicate_ids={duplicate_ids} "
            f"converted={dict(converted)} status={dict(status_counts)}"
        )

    write_csv(OVERVIEW_OUT, overview_fields, cleaned_overview)
    write_csv(ISSUES_OUT, issue_fields, cleaned)

    created = [row["created_on"] for row in cleaned]
    recorded_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"recorded_at: {recorded_at}")
    print(f"issue_rows: {len(cleaned)}")
    print(f"overview_rows: {len(cleaned_overview)}")
    for name in DATE_COLUMNS:
        print(f"converted {name}: {converted[name]}")
    print(f"created_on_sample: {issues[0]['created_on'].strip()} -> {cleaned[0]['created_on']}")
    print(f"created_on_min: {min(created)}")
    print(f"created_on_max: {max(created)}")
    print(f"wrote {OVERVIEW_OUT}")
    print(f"wrote {ISSUES_OUT}")


if __name__ == "__main__":
    main()
