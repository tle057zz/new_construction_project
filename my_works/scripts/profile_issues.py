"""Profile the raw issue workbook. Does not modify the workbook.

Writes docs/data_dictionary.csv and validation/value_counts.csv.
Does not calculate resolution time or overdue.
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
DICTIONARY = ROOT / "docs" / "data_dictionary.csv"
VALUE_COUNTS = ROOT / "validation" / "value_counts.csv"
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


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not RAW.is_file():
        raise SystemExit(f"raw workbook not found: {RAW}")
    if len(SQL_NAMES) != 53:
        raise SystemExit(f"expected 53 SQL names, found {len(SQL_NAMES)}")

    book = ZipFile(RAW)
    workbook = ET.fromstring(book.read("xl/workbook.xml"))
    sheet_names = [node.get("name") for node in workbook.findall("m:sheets/m:sheet", NS)]
    strings_root = ET.fromstring(book.read("xl/sharedStrings.xml"))
    strings = [
        "".join((node.text or "") for node in item.findall(".//m:t", NS))
        for item in strings_root.findall("m:si", NS)
    ]
    overview = sheet_rows(book, "xl/worksheets/sheet1.xml", strings)
    issues = sheet_rows(book, "xl/worksheets/sheet2.xml", strings)
    header = [value for value, _kind in issues[0]]
    data = issues[1:]
    if len(header) != 53:
        raise SystemExit(f"expected 53 columns, found {len(header)}")

    ids = [row[0][0] for row in data]
    blank_ids = sum(1 for item in ids if not nonblank(item))
    duplicate_ids = sum(1 for count in Counter(ids).values() if count > 1)

    seen: Counter[str] = Counter()
    dictionary = []
    for index, name in enumerate(header):
        seen[name] += 1
        pairs = [row[index] for row in data]
        present = [value for value, _kind in pairs if nonblank(value)]
        kinds = Counter(kind for _value, kind in pairs if kind != "empty")
        note = ""
        if seen[name] > 1:
            note = f"Repeated Excel header. Occurrence {seen[name]}."
        if kinds.get("number") and kinds.get("text"):
            note = "Mixed numeric serials and text. Blank text is not a value. Not converted."
        elif kinds.get("number") and not kinds.get("text"):
            note = "Excel serial number. Not converted."
        elif not present:
            note = "Header is present. No non-blank values."
        dictionary.append({
            "excel_column": index + 1,
            "excel_header": name,
            "header_occurrence": seen[name],
            "sql_name": SQL_NAMES[index],
            "nonblank_values": len(present),
            "distinct_nonblank": len(set(present)),
            "number_cells": kinds.get("number", 0),
            "text_cells": kinds.get("text", 0),
            "note": note,
        })
    write_csv(DICTIONARY, dictionary)

    value_rows = []
    for index, name in enumerate(header):
        counts = Counter(row[index][0].strip() for row in data if nonblank(row[index][0]))
        if not counts or len(counts) > 40:
            continue
        for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            value_rows.append({
                "excel_header": name,
                "header_occurrence": dictionary[index]["header_occurrence"],
                "sql_name": SQL_NAMES[index],
                "value": value,
                "rows": count,
            })
    write_csv(VALUE_COUNTS, value_rows)

    overview_values = [
        value for row in overview for value, _kind in row if nonblank(value)
    ]
    recorded_at = datetime.now().astimezone().isoformat(timespec="seconds")
    print(f"recorded_at: {recorded_at}")
    print(f"source: {RAW}")
    print(f"sheets: {', '.join(sheet_names)}")
    print(f"overview_nonblank_cells: {len(overview_values)}")
    print("overview_values: " + " | ".join(overview_values))
    print(f"issue_rows: {len(data)}")
    print(f"issue_columns: {len(header)}")
    print(f"unique_ids: {len(set(ids))}")
    print(f"blank_ids: {blank_ids}")
    print(f"duplicate_ids: {duplicate_ids}")
    print(f"wrote {DICTIONARY}")
    print(f"wrote {VALUE_COUNTS}")


if __name__ == "__main__":
    main()
