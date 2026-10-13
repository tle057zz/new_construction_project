"""Ingest the raw issue workbook into staged CSV files.

Reads the raw workbook only. Does not modify it.
Keeps original cell text and numeric serials. Does not convert dates.
Writes Overview and Issues as separate files.
Replaces the staged files on each run.
"""

from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "Snowden Towers Sample Issue Summary.xlsx"
STAGED = ROOT / "data" / "staged"
OVERVIEW_OUT = STAGED / "overview.csv"
ISSUES_OUT = STAGED / "issues.csv"
SOURCE_FILE = RAW.name
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

SQL_NAMES = [
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
    "warranty_info", "warranty_number", "work_order_number",
]

EXPECTED_HEADERS = [
    "ID", "Title", "Status", "Category", "Type", "Description", "Assigned to",
    "Company", "Watchers", "Created by", "Created on", "Due date", "Start date",
    "Location", "Location details", "Placement", "Root cause", "Published",
    "Updated by", "Updated on", "Closed by", "Closed at", "Comments",
    "Additional Comments", "Areas Affected", "Building Element", "Cost Impact?",
    "Date Received", "Defect", "Did you Link an Asset? - You should link an asset",
    "Facilities Team Review Status", "Hyperlink", "Hyperlink", "Install Date",
    "Interface Topic", "Lessons Learned Candidate?", "Multi-select dropdown",
    "Numeric", "Part Number", "Project Task Code", "Quality Issue with Cost",
    "Review Status", "Risk Level", "Row", "SC Acknowledged", "Seat",
    "Serial Number", "Serial Number", "Ship Date", "Size", "Warranty Info",
    "Warranty Number", "Work Order #",
]


def col_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    number = 0
    for ch in letters:
        number = number * 26 + (ord(ch) - 64)
    return number - 1


def cell_text(cell: ET.Element, strings: list[str]) -> tuple[str, str]:
    kind = cell.get("t") or "n"
    node = cell.find("m:v", NS)
    if node is None or node.text is None:
        return "", "empty"
    raw = node.text
    if kind == "s":
        return strings[int(raw)], "text"
    return raw, "number"


def sheet_cells(book: ZipFile, sheet_path: str, strings: list[str]) -> list[tuple[str, str, str]]:
    root = ET.fromstring(book.read(sheet_path))
    cells = []
    for row in root.findall("m:sheetData/m:row", NS):
        for cell in row.findall("m:c", NS):
            value, kind = cell_text(cell, strings)
            cells.append((cell.get("r"), value, kind))
    return cells


def sheet_rows(book: ZipFile, sheet_path: str, strings: list[str]) -> list[list[tuple[str, str]]]:
    root = ET.fromstring(book.read(sheet_path))
    parsed = []
    width = 0
    for row in root.findall("m:sheetData/m:row", NS):
        cells: dict[int, tuple[str, str]] = {}
        for cell in row.findall("m:c", NS):
            index = col_index(cell.get("r"))
            cells[index] = cell_text(cell, strings)
            width = max(width, index + 1)
        parsed.append([cells.get(i, ("", "empty")) for i in range(width)])
    return parsed


def nonblank(value: str) -> bool:
    return value.strip() != ""


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not RAW.is_file():
        raise SystemExit(f"raw workbook not found: {RAW}")
    if len(SQL_NAMES) != 53 or len(EXPECTED_HEADERS) != 53:
        raise SystemExit("expected 53 column names")

    book = ZipFile(RAW)
    workbook = ET.fromstring(book.read("xl/workbook.xml"))
    sheet_names = [node.get("name") for node in workbook.findall("m:sheets/m:sheet", NS)]
    if sheet_names != ["Overview", "Issues"]:
        raise SystemExit(f"unexpected sheets: {sheet_names}")

    strings_root = ET.fromstring(book.read("xl/sharedStrings.xml"))
    strings = [
        "".join((node.text or "") for node in item.findall(".//m:t", NS))
        for item in strings_root.findall("m:si", NS)
    ]
    ingested_at = datetime.now().astimezone().isoformat(timespec="seconds")

    overview_cells = [
        (ref, value, kind)
        for ref, value, kind in sheet_cells(book, "xl/worksheets/sheet1.xml", strings)
        if nonblank(value)
    ]
    overview_rows = [
        {
            "excel_cell": ref,
            "value": value,
            "value_kind": kind,
            "source_file": SOURCE_FILE,
            "source_sheet": "Overview",
            "ingestion_timestamp": ingested_at,
        }
        for ref, value, kind in overview_cells
    ]

    issues = sheet_rows(book, "xl/worksheets/sheet2.xml", strings)
    header = [value for value, _kind in issues[0]]
    data = issues[1:]
    if header != EXPECTED_HEADERS:
        raise SystemExit("Issues header does not match the profiled columns")

    ids = [row[0][0] for row in data]
    blank_ids = sum(1 for item in ids if not nonblank(item))
    duplicate_ids = sum(count - 1 for count in Counter(ids).values() if count > 1)
    if len(data) != 289 or len(set(ids)) != 289 or blank_ids or duplicate_ids:
        raise SystemExit(
            f"issue check failed: rows={len(data)} unique={len(set(ids))} "
            f"blank_ids={blank_ids} duplicate_ids={duplicate_ids}"
        )

    issue_fields = SQL_NAMES + ["source_file", "source_sheet", "ingestion_timestamp"]
    issue_rows = []
    for row in data:
        record = {name: row[index][0] for index, name in enumerate(SQL_NAMES)}
        record["source_file"] = SOURCE_FILE
        record["source_sheet"] = "Issues"
        record["ingestion_timestamp"] = ingested_at
        issue_rows.append(record)

    write_csv(
        OVERVIEW_OUT,
        ["excel_cell", "value", "value_kind", "source_file", "source_sheet", "ingestion_timestamp"],
        overview_rows,
    )
    write_csv(ISSUES_OUT, issue_fields, issue_rows)

    print(f"ingestion_timestamp: {ingested_at}")
    print(f"overview_rows: {len(overview_rows)}")
    print(f"issue_rows: {len(issue_rows)}")
    print(f"issue_columns: {len(issue_fields)}")
    print(f"unique_ids: {len(set(ids))}")
    print(f"wrote {OVERVIEW_OUT}")
    print(f"wrote {ISSUES_OUT}")


if __name__ == "__main__":
    main()
