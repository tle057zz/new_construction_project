"""Record lineage for the raw issue workbook. Does not modify the workbook."""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SOURCE = REPO / "Project Files" / "04_Reports" / "Snowden Towers Sample Issue Summary.xlsx"
RAW = ROOT / "data" / "raw" / "Snowden Towers Sample Issue Summary.xlsx"
LINEAGE = ROOT / "data" / "raw" / "lineage.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_timestamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"source workbook not found: {SOURCE}")
    if not RAW.is_file():
        raise SystemExit(f"raw workbook not found: {RAW}")

    source_hash = sha256(SOURCE)
    raw_hash = sha256(RAW)
    recorded_at = datetime.now().astimezone().isoformat(timespec="seconds")
    row = {
        "source_file": SOURCE.name,
        "source_path": "Project Files/04_Reports/Snowden Towers Sample Issue Summary.xlsx",
        "raw_path": "my_works/data/raw/Snowden Towers Sample Issue Summary.xlsx",
        "sha256": raw_hash,
        "source_sha256": source_hash,
        "hashes_match": str(source_hash == raw_hash),
        "source_modified_at": local_timestamp(SOURCE),
        "raw_modified_at": local_timestamp(RAW),
        "recorded_at": recorded_at,
    }
    with LINEAGE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)

    print(f"wrote {LINEAGE}")
    for key, value in row.items():
        print(f"{key}: {value}")
    if source_hash != raw_hash:
        raise SystemExit("raw workbook checksum does not match the source workbook")


if __name__ == "__main__":
    main()
