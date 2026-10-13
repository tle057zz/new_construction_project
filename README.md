# Snowdon Towers

Practice record for Autodesk Forma’s **Construction: Sample Project – Snowdon Towers**, plus a traceable issue pipeline from the sample workbook through Python, SQLite, and Power BI.

The reporting source is `Snowden Towers Sample Issue Summary.xlsx` (Autodesk’s spelling of the file name). It has 289 issue rows, 53 columns, and a unique ID on every row. This project is separate from any USACE procurement RFI register. Three issue rows typed RFI stay rows in this workbook.

## Layout

```text
Project Files/          14 sample files in five type folders
my_works/               issue pipeline: raw, staged, curated, SQL, Power BI
web_reports/            baseline reports and the Power BI step pages
snowdon_markdown/       roadmap, Forma steps, and the pipeline plan
```

`Project Files` holds the local download:

| Folder | Contents |
|---|---|
| `01_Design Files` | Five PDF sheets and one multipage structural PDF |
| `02_Drawings` | Five DWG files |
| `03_Models` | `Snowdon Towers Sample Structural.rvt` |
| `04_Reports` | `Snowden Towers Sample Issue Summary.xlsx` |
| `05_Contracts` | One subcontract agreement (DOCX) |

An unchanged copy of the workbook sits in `my_works/data/raw/`. `my_works/data/raw/lineage.csv` records that the raw copy matches the file under `Project Files`.

## Reports

Open `web_reports/index.html` in a browser. The pages are static HTML and do not need a server. Read them in order:

1. Baseline status
2. Project structure in Forma
3. Project Files register
4. Inspection of S102 in Forma
5. Structural model
6. Issue workbook
7. Finish CDE setup
8. Path to Power BI, then the step pages under it: lineage, profile, ingest, clean, SQL, reconcile, measures, and the report pages

The step pages under report 08 are regenerated from the files on disk. The path page, the overview page, and the lifecycle page are maintained on their own.

## Pipeline

Python 3.10 or newer. The scripts use the standard library only.

Run them from `my_works/scripts`, in this order. Each script reads the previous layer and replaces its own outputs.

```bash
cd my_works/scripts
python3 record_lineage.py    # checksum of the raw workbook against Project Files
python3 profile_issues.py    # docs/data_dictionary.csv, validation/value_counts.csv
python3 ingest_issues.py     # data/staged/overview.csv and issues.csv
python3 clean_issues.py      # data/curated/; Excel date serials become timestamps
python3 load_issues.py       # sql/snowdon_issues.sqlite from sql/01_issues.sql
python3 reconcile_issues.py  # validation/reconcile.csv
python3 measure_issues.py    # validation/measures.csv
python3 export_powerbi.py    # powerbi/fact_issues.csv and the three lookups
python3 build_report_pages.py  # rewrite the report 08 step pages
```

`reconcile_issues.py` imports `ingest_issues`, so the working directory has to be `my_works/scripts`.

What each layer keeps:

| Layer | Path | What it holds |
|---|---|---|
| Raw | `my_works/data/raw/` | Unchanged workbook, plus the lineage row |
| Staged | `my_works/data/staged/` | Original cell text. Overview is 10 cover cells. Issues is 289 rows, with `source_file`, `source_sheet`, and `ingestion_timestamp` |
| Curated | `my_works/data/curated/` | Same rows, with created, updated, due, start, and closed dates converted where the cell was a serial |
| SQL | `my_works/sql/snowdon_issues.sqlite` | `overview`, `issue_rows`, `fact_issues`, `dim_status` (9), `dim_category` (18), `dim_type` (33) |
| Power BI | `my_works/powerbi/` | `fact_issues.csv`, `dim_status.csv`, `dim_category.csv`, `dim_type.csv`, and `vis.pbix` |

`fact_issues` is one row per issue ID. The three lookups join many-to-one into that fact on `status_id`, `category_id`, and `type_id`. A count of `id` with no filter is 289.

Status counts in the workbook, and after every later layer: Open 148, In dispute 51, Draft 46, Closed 11, Completed 11, In progress 7, Pending 7, Not approved 5, In review 3. Closed and Completed stay separate labels. Assignee, company, watchers, and created-by are Autodesk on all 289 rows.

## Power BI

`my_works/powerbi/vis.pbix` loads the four CSV files. Report 08 records the model check: three active relationships, filter direction from each lookup into `fact_issues`. The published pages linked from `web_reports/08-path-to-power-bi.html` are Issue Executive Overview and Issue Lifecycle & Overdue Monitoring. The HTML executive and issues pages are a local view of the same 289 rows.

## Limits

- The Forma account did not yield a files log, a version history export, or a review-event export. There is no document, version, review, discipline, or calendar table.
- The hand-written file register in the HTML reports describes the local copies. It is not a Forma extract.
- The Python measures do not calculate resolution time. Closed at is filled on 14 rows, which is not the same set as the Closed and Completed status labels.
- Due date is blank on 47 rows, location on 208, description on 157, and root cause on 171. Those blanks stay blank.

## Planning notes

- `snowdon_markdown/01-snowdon-towers-full-roadmap.md` — where the practice sits, and the end-to-end steps
- `snowdon_markdown/02-forma-hands-on-steps.md` — Forma Data Management actions
- `snowdon_markdown/03-python-sql-powerbi-plan.md` — acquisition, model, and validation plan
