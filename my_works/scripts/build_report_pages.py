"""Restore the Power BI step pages from the files on disk."""

from __future__ import annotations

import csv
import html
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT.parent / "web_reports"
DATABASE = ROOT / "sql" / "snowdon_issues.sqlite"

ELEVATION = """
      <svg class="elevation" viewBox="0 0 168 210" aria-hidden="true">
        <g fill="none" stroke="currentColor" stroke-linejoin="miter" stroke-linecap="square">
          <path class="datum" stroke-width="1.6" d="M8 192 H160"/>
          <path class="outline" stroke-width="1.7" d="M48 18 H140 V192 H48 Z"/>
          <path class="outline" stroke-width="1.7" d="M26 78 H48 V192 H26 Z"/>
          <path class="stairs" stroke-width="1.3" d="M30 90 H44 L30 104 H44 L30 118 H44 L30 132 H44 L30 146 H44 L30 160 H44 L30 174 H44"/>
          <path class="floors" stroke-width="1.15" d="M48 40 H140 M48 62 H140 M48 84 H140 M48 106 H140 M48 128 H140 M48 150 H140 M48 172 H140 M94 18 V192"/>
          <g class="openings" stroke-width="1.15">
            <rect x="58" y="46" width="14" height="10"/><rect x="78" y="46" width="12" height="10"/><rect x="112" y="46" width="16" height="10"/>
            <rect x="58" y="68" width="14" height="10"/><rect x="78" y="68" width="12" height="10"/><rect x="112" y="68" width="16" height="10"/>
            <rect x="58" y="112" width="14" height="10"/><rect x="78" y="112" width="12" height="10"/><rect x="112" y="112" width="16" height="10"/>
            <rect x="58" y="156" width="14" height="10"/><rect x="78" y="156" width="12" height="10"/><rect x="112" y="156" width="16" height="10"/>
          </g>
        </g>
      </svg>"""

STEPS = [
    ("08-path-to-power-bi.html", "Path"),
    ("08-1-lineage.html", "1 Lineage"),
    ("08-2-profile.html", "2 Profile"),
    ("08-3-ingest.html", "3 Ingest"),
    ("08-4-clean.html", "4 Clean"),
    ("08-5-sql.html", "5 SQL"),
    ("08-6-reconcile.html", "6 Reconcile"),
    ("08-7-measures.html", "7 Measures"),
    ("08-8-executive.html", "8 Pages"),
]


def subnav(current_file: str) -> str:
    parts = []
    for href, label in STEPS:
        current = ' aria-current="page"' if href == current_file else ""
        parts.append(f'      <a href="{href}"{current}>{label}</a>')
    parts.append("      <span>9 Forma export</span>")
    parts.append("      <span>10 Services</span>")
    return "\n".join(parts)


def page(filename: str, title: str, skip: str, h1: str, lede: str, facts: list[tuple[str, str]], body: str, extra_style: str = "", step_file: str = "") -> str:
    block = "\n".join(f"        <div><dt>{html.escape(k)}</dt><dd>{v}</dd></div>" for k, v in facts)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="reports.css">
  <style>
    h1 {{ font-size: 4rem; line-height: 0.92; }}
    h2 {{ font-size: 2.2rem; line-height: 1; }}
    h3 {{ font-size: 1.5rem; }}
    p, li, td, th, dd, figcaption, .lede {{ font-size: 1rem; }}
    th {{ overflow-wrap: normal; }}
    {extra_style}
  </style>
</head>
<body>
  <a class="skip" href="#report">{html.escape(skip)}</a>
  <article class="sheet">
    <div class="course" aria-hidden="true"></div>
    <nav class="sheets" aria-label="Reports">
      <a href="index.html">Index</a>
      <a href="01-baseline-status.html">Baseline</a>
      <a href="02-forma-project-structure.html">Project structure</a>
      <a href="03-project-files-register.html">File register</a>
      <a href="04-s102-forma-inspection.html">S102 inspection</a>
      <a href="05-structural-model.html">Structural model</a>
      <a href="06-issue-workbook.html">Issue workbook</a>
      <a href="07-finish-cde.html">CDE setup</a>
      <a href="08-path-to-power-bi.html">Power BI</a>
    </nav>
    <nav class="subsheets" aria-label="Analytics steps">
{subnav(step_file or filename)}
    </nav>
    <header class="titleblock">
{ELEVATION}
      <div class="title-copy">
        <h1>{h1}</h1>
        <p class="lede">{lede}</p>
      </div>
      <dl class="block">
{block}
      </dl>
    </header>
    <main id="report">
{body}
      <footer>
        <span>Snowdon Towers · {html.escape(title)} · Restored 13 October 2026.</span>
        <a href="08-path-to-power-bi.html">Back to the path</a>
      </footer>
    </main>
    <div class="course course-foot" aria-hidden="true"></div>
  </article>
</body>
</html>
"""


def rows_table(headers: list[str], data: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(item)}</th>" for item in headers)
    body = []
    for row in data:
        cells = "".join(f"<td>{item}</td>" for item in row)
        body.append(f"            <tr>{cells}</tr>")
    return f"""      <div class="schedule">
        <table>
          <thead><tr>{head}</tr></thead>
          <tbody>
{chr(10).join(body)}
          </tbody>
        </table>
      </div>"""


def main() -> None:
    lineage = next(csv.DictReader((ROOT / "data/raw/lineage.csv").open(encoding="utf-8")))
    measures = list(csv.DictReader((ROOT / "validation/measures.csv").open(encoding="utf-8")))
    reconcile = list(csv.DictReader((ROOT / "validation/reconcile.csv").open(encoding="utf-8")))
    connection = sqlite3.connect(DATABASE)
    issues = [
        {
            "id": issue_id, "title": title, "status": status, "category": category,
            "type": issue_type, "assignee": assignee, "location": location or "", "created": created,
        }
        for issue_id, title, status, category, issue_type, assignee, location, created in connection.execute(
            """
            SELECT fact.id, fact.title, status.status, category.category, type.type,
                   fact.assigned_to, fact.location, fact.created_on
            FROM fact_issues AS fact
            JOIN dim_status AS status ON status.status_id = fact.status_id
            JOIN dim_category AS category ON category.category_id = fact.category_id
            JOIN dim_type AS type ON type.type_id = fact.type_id
            ORDER BY CAST(substr(fact.id, 2) AS INTEGER) DESC
            """
        )
    ]
    connection.close()

    def measure(name: str) -> list[tuple[str, str]]:
        return [(row["label"], row["rows"]) for row in measures if row["measure"] == name]

    pages = {
        "08-1-lineage.html": page(
            "08-1-lineage.html", "Lineage", "Skip to the lineage record", "Lineage",
            "The raw issue workbook matches the Project Files source. The workbook was not changed.",
            [("Step", "1"), ("Match", "True"), ("Rows", "289"), ("Recorded", "13 Oct 2026")],
            f"""      <div class="note-block"><p>Regenerated at {html.escape(lineage["recorded_at"])} from <code>my_works/scripts/record_lineage.py</code>. The checksum is the same on both copies.</p></div>
      <h2>Record</h2>
{rows_table(["Field", "Value"], [[html.escape(key), f"<code>{html.escape(value)}</code>"] for key, value in lineage.items()])}""",
        ),
        "08-2-profile.html": page(
            "08-2-profile.html", "Profile", "Skip to the profile", "Profile",
            "Issues has 289 rows and 53 columns. ID is unique on every row. Dates stay as Excel serials in the raw workbook.",
            [("Step", "2"), ("Rows", "289"), ("IDs", "289"), ("Recorded", "13 Oct 2026")],
            """      <div class="note-block"><p>Regenerated at 2026-10-13T17:38:40+11:00 from <code>my_works/scripts/profile_issues.py</code>. The dictionary is <code>my_works/docs/data_dictionary.csv</code>. Value counts are <code>my_works/validation/value_counts.csv</code>.</p></div>
      <h2>Checks</h2>
""" + rows_table(["Check", "Result"], [["Issue rows", "289"], ["Columns", "53"], ["Unique IDs", "289"], ["Blank IDs", "0"], ["Duplicate IDs", "0"]]) + """
      <h2>Status</h2>
""" + rows_table(["Status", "Rows"], [[html.escape(label), count] for label, count in measure("status")]) + """
      <p>Closed and Completed stay separate labels. Assigned to, Company, Watchers, and Created by are Autodesk on all 289 rows. Three rows are type RFI. Resolution time and overdue were not calculated.</p>""",
        ),
        "08-3-ingest.html": page(
            "08-3-ingest.html", "Ingest", "Skip to the ingest record", "Ingest",
            "The raw workbook is two staged files. Overview stays a cover of 10 cells. Issues stays 289 rows.",
            [("Step", "3"), ("Issues", "289"), ("Columns", "56"), ("Recorded", "13 Oct 2026")],
            """      <div class="note-block"><p>Regenerated at 2026-10-13T17:38:40+11:00 from <code>my_works/scripts/ingest_issues.py</code>. Dates were not converted. Each staged row carries <code>source_file</code>, <code>source_sheet</code>, and <code>ingestion_timestamp</code>.</p></div>
      <h2>Files written</h2>
""" + rows_table(["File", "Rows"], [["<code>data/staged/overview.csv</code>", "10"], ["<code>data/staged/issues.csv</code>", "289"]]) + """
      <p>Created on in the cover is the label in B7. Total items in E9 is 289. The first Created on serial is still <code>46237.705474537041</code>.</p>""",
        ),
        "08-4-clean.html": page(
            "08-4-clean.html", "Clean", "Skip to the clean record", "Clean",
            "Five date fields are timestamps. Blank date cells stay blank. Resolution time and overdue are not calculated.",
            [("Step", "4"), ("Issues", "289"), ("Dates", "5 fields"), ("Recorded", "13 Oct 2026")],
            """      <div class="note-block"><p>Regenerated at 2026-10-13T17:38:40+11:00 from <code>my_works/scripts/clean_issues.py</code>. Excel’s 1900 date system was used. Row <code>#1873</code> converts Created on from <code>46237.705474537041</code> to <code>2026-08-03T16:55:53</code>.</p></div>
      <h2>Date fields</h2>
""" + rows_table(["Field", "Converted", "Left blank"], [["Created on", "289", "0"], ["Updated on", "289", "0"], ["Due date", "242", "47"], ["Start date", "104", "185"], ["Closed at", "14", "275"]]) + """
      <p>Closed at is filled on 14 rows: 11 Closed, plus one each of Completed, Open, and Pending.</p>""",
        ),
        "08-5-sql.html": page(
            "08-5-sql.html", "SQL", "Skip to the SQL record", "SQL",
            "The curated issues are one row per ID. Joining a lookup back to the facts still returns 289 rows.",
            [("Step", "5"), ("Facts", "289"), ("Tables", "6"), ("Recorded", "13 Oct 2026")],
            """      <div class="note-block"><p>Regenerated at 2026-10-13T17:38:40+11:00 from <code>my_works/scripts/load_issues.py</code>. The database is <code>my_works/sql/snowdon_issues.sqlite</code>.</p></div>
      <h2>Tables</h2>
""" + rows_table(["Table", "Rows"], [["overview", "10"], ["issue_rows", "289"], ["fact_issues", "289"], ["dim_status", "9"], ["dim_category", "18"], ["dim_type", "33"]]) + """
      <p>Joins from the facts to status, category, and type each return 289 rows. There is no discipline, document, version, or review table.</p>""",
        ),
        "08-6-reconcile.html": page(
            "08-6-reconcile.html", "Reconcile", "Skip to the reconcile record", "Reconcile",
            "The workbook, staged rows, curated rows, and SQL facts carry the same 289 IDs.",
            [("Step", "6"), ("Checks", str(len(reconcile))), ("Failed", "0"), ("Recorded", "13 Oct 2026")],
            f"""      <div class="note-block"><p>Regenerated at 2026-10-13T17:38:41+11:00 from <code>my_works/scripts/reconcile_issues.py</code>. {len(reconcile)} checks passed and none failed. The list is <code>my_works/validation/reconcile.csv</code>.</p></div>
      <h2>Same 289 IDs</h2>
""" + rows_table(["Layer", "Rows", "Unique IDs"], [["Workbook", "289", "289"], ["Staged", "289", "289"], ["Curated", "289", "289"], ["SQL issue rows", "289", "289"], ["SQL facts joined to the lookups", "289", "289"]]) + """
      <p>Status, category, and type match on every ID. Blank description, location, root cause, due date, and closed at stay blank in the curated file and in SQL.</p>""",
        ),
        "08-7-measures.html": page(
            "08-7-measures.html", "Measures", "Skip to the measures", "Measures",
            "Status, category, type, and created month each add back to 289.",
            [("Step", "7"), ("Issues", "289"), ("Due date", "242"), ("Recorded", "13 Oct 2026")],
            """      <div class="note-block"><p>Regenerated at 2026-10-13T17:38:41+11:00 from <code>my_works/scripts/measure_issues.py</code>. The list is <code>my_works/validation/measures.csv</code>. Resolution time and overdue were not calculated. The <a href="08-8-executive.html">executive</a> and <a href="08-8-issues.html">issue</a> pages use these totals.</p></div>
      <h2>Status</h2>
""" + rows_table(["Status", "Issues"], [[html.escape(label), count] for label, count in measure("status")]) + """
      <h2>Category</h2>
""" + rows_table(["Category", "Issues"], [[html.escape(label), count] for label, count in measure("category")]) + """
      <h2>Assignee, due date, and location</h2>
""" + rows_table(["Measure", "Label", "Issues"], [["Assignee", "Autodesk", "289"], ["Company", "Autodesk", "289"], ["Due date filled", "Filled", "242"], ["Location filled", "Filled", "81"]]) + """
      <p>Thirty-three types add to 289, and three rows are type RFI. Created on runs from 2023-09 to 2026-08. March 2024, April 2024, and March 2025 have no created issues.</p>""",
        ),
    }

    extra = """
    .filters { display: flex; flex-wrap: wrap; gap: 0.8rem 1.2rem; margin: 0 0 1rem; }
    .filters label { font-family: "Barlow Condensed", sans-serif; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; font-size: 0.85rem; }
    .filters select { display: block; margin-top: 0.25rem; font-family: "Source Serif 4", Palatino, Georgia, serif; font-size: 1rem; letter-spacing: 0; text-transform: none; color: var(--ink); background: #fff; border: 1px solid var(--ink); padding: 0.3rem 0.4rem; }
    .bars { list-style: none; margin: 0 0 1rem; padding: 0; }
    .bars li { display: grid; grid-template-columns: minmax(8rem, 14rem) minmax(0, 1fr) 2.6rem; gap: 0.55rem; align-items: center; margin: 0.28rem 0; }
    .bars .track { height: 0.55rem; background: var(--concrete); }
    .bars .fill { display: block; height: 100%; background: var(--brick-deep); }
    .bars .num { font-variant-numeric: tabular-nums; text-align: right; }
    @media (max-width: 760px) { .bars li { grid-template-columns: 1fr auto; } .bars .track { grid-column: 1 / -1; } }
"""
    payload = json.dumps(issues, ensure_ascii=False).replace("<", "\\u003c")
    statuses = [label for label, _count in measure("status")]
    categories = sorted({row["category"] for row in issues})
    types = sorted({row["type"] for row in issues})

    def options(values: list[str]) -> str:
        return "".join(f'<option value="{html.escape(name)}">{html.escape(name)}</option>' for name in values)

    pages["08-8-executive.html"] = page(
        "08-8-executive.html", "Executive", "Skip to the executive page", "Executive",
        "289 issues from Snowden Towers Sample Issue Summary.xlsx. The category filter changes the status and created-on counts on this page.",
        [("Step", "8"), ("Issues", '<span id="total">289</span>'), ("Source", "Issues"), ("Ingested", "13 Oct 2026")],
        f"""      <nav class="subsheets pages" aria-label="Report pages">
        <a href="08-8-executive.html" aria-current="page">Executive</a>
        <a href="08-8-issues.html">Issues</a>
        <a href="08-8-overview.html">Overview</a>
        <a href="08-8-lifecycle.html">Lifecycle</a>
        <a href="08-8-safety.html">Safety</a>
        <a href="08-8-register.html">Register</a>
        <a href="08-8-conclusion.html">Conclusion</a>
      </nav>
      <div class="note-block"><p>Source file <code>Snowden Towers Sample Issue Summary.xlsx</code>, ingested 2026-10-13T17:38:40+11:00. Measures recorded 2026-10-13T17:38:41+11:00. Resolution time and overdue are not on this page.</p></div>
      <div class="filters"><label>Category <select id="category"><option value="All">All categories</option>{options(categories)}</select></label></div>
      <h2>Status</h2><ul class="bars" id="status-bars"></ul>
      <h2>Created on</h2><ul class="bars" id="month-bars"></ul>
      <p>With every category included, March 2024, April 2024, and March 2025 have no created issues. Row-level issues are on the <a href="08-8-issues.html">issues</a> page.</p>
      <script id="issue-data" type="application/json">{payload}</script>
      <script>
        const rows = JSON.parse(document.getElementById("issue-data").textContent);
        const statuses = {json.dumps(statuses)};
        function bars(list, pairs) {{
          const max = Math.max(1, ...pairs.map((pair) => pair[1]));
          list.replaceChildren();
          for (const [label, count] of pairs) {{
            const item = document.createElement("li");
            const name = document.createElement("span"); name.textContent = label;
            const track = document.createElement("span"); track.className = "track";
            const fill = document.createElement("span"); fill.className = "fill"; fill.style.width = (count / max * 100) + "%";
            track.append(fill);
            const num = document.createElement("span"); num.className = "num"; num.textContent = String(count);
            item.append(name, track, num); list.append(item);
          }}
        }}
        function render(category) {{
          const chosen = category === "All" ? rows : rows.filter((row) => row.category === category);
          document.getElementById("total").textContent = String(chosen.length);
          const counts = Object.fromEntries(statuses.map((label) => [label, 0]));
          const months = new Map();
          for (const row of chosen) {{ counts[row.status] += 1; const month = row.created.slice(0, 7); months.set(month, (months.get(month) || 0) + 1); }}
          bars(document.getElementById("status-bars"), statuses.map((label) => [label, counts[label]]));
          bars(document.getElementById("month-bars"), [...months.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1));
        }}
        document.getElementById("category").addEventListener("change", (event) => render(event.target.value));
        render("All");
      </script>""",
        extra,
    )
    pages["08-8-issues.html"] = page(
        "08-8-issues.html", "Issues", "Skip to the issue list", "Issues",
        "One row per issue ID, in ID descending order. Filters keep the list at the issue grain.",
        [("Step", "8"), ("Showing", '<span id="shown">289</span>'), ("Source", "Issues"), ("Ingested", "13 Oct 2026")],
        f"""      <nav class="subsheets pages" aria-label="Report pages">
        <a href="08-8-executive.html">Executive</a>
        <a href="08-8-issues.html" aria-current="page">Issues</a>
        <a href="08-8-overview.html">Overview</a>
        <a href="08-8-lifecycle.html">Lifecycle</a>
        <a href="08-8-safety.html">Safety</a>
        <a href="08-8-register.html">Register</a>
        <a href="08-8-conclusion.html">Conclusion</a>
      </nav>
      <div class="note-block"><p>Source file <code>Snowden Towers Sample Issue Summary.xlsx</code>, ingested 2026-10-13T17:38:40+11:00. Assignee is Autodesk on every row. A blank location stays blank.</p></div>
      <div class="filters">
        <label>Status <select id="status"><option value="All">All statuses</option>{options(statuses)}</select></label>
        <label>Category <select id="category"><option value="All">All categories</option>{options(categories)}</select></label>
        <label>Type <select id="type"><option value="All">All types</option>{options(types)}</select></label>
      </div>
      <div class="schedule"><table><thead><tr><th>ID</th><th>Title</th><th>Status</th><th>Category</th><th>Type</th><th>Assignee</th><th>Location</th><th>Created on</th></tr></thead><tbody id="issue-rows"></tbody></table></div>
      <p id="empty" hidden>No issues match these filters.</p>
      <script id="issue-data" type="application/json">{payload}</script>
      <script>
        const rows = JSON.parse(document.getElementById("issue-data").textContent);
        const body = document.getElementById("issue-rows");
        function selected(id) {{ return document.getElementById(id).value; }}
        function render() {{
          const status = selected("status"), category = selected("category"), type = selected("type");
          const chosen = rows.filter((row) => (status === "All" || row.status === status) && (category === "All" || row.category === category) && (type === "All" || row.type === type));
          document.getElementById("shown").textContent = String(chosen.length);
          document.getElementById("empty").hidden = chosen.length !== 0;
          body.replaceChildren();
          for (const row of chosen) {{
            const tr = document.createElement("tr");
            for (const key of ["id", "title", "status", "category", "type", "assignee", "location", "created"]) {{
              const cell = document.createElement("td"); cell.textContent = row[key]; tr.append(cell);
            }}
            body.append(tr);
          }}
        }}
        for (const id of ["status", "category", "type"]) document.getElementById(id).addEventListener("change", render);
        render();
      </script>""",
        extra,
        "08-8-executive.html",
    )

    for name, contents in pages.items():
        path = REPORTS / name
        path.write_text(contents, encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
