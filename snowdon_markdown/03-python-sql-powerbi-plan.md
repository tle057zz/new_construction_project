# Snowdon Towers: Data Pipeline and Power BI Implementation Plan

## Objective

Build a reliable analytics pipeline using **actual available Forma exports and/or the Snowdon Towers issue-summary workbook**, then Python, SQL and Power BI. Do not assume the sample project contains real RFI, review, or revision-history tables.

## 1. Data acquisition

### Inputs

1. `Snowden Towers Sample Issue Summary.xlsx` (available locally).
2. A Forma Data Management Files Log/document export, **if supported by the account**.
3. Forma issues export, **if enabled**.
4. API response data, as a later optional extension.

### Suggested directories

```text
snowdon_analytics/
├── data/
│   ├── raw/
│   ├── staged/
│   └── curated/
├── scripts/
├── sql/
├── powerbi/
├── validation/
└── docs/
```

Preserve source files in `data/raw/` unchanged. Store retrieval time, file name, source platform, and schema details.

## 2. Source profiling

For each input:

- Inspect columns and data types.
- Record source and sheet name.
- Count total rows and unique IDs.
- Assess nulls and duplicates.
- Determine whether records are snapshots, issues, documents, versions, or events.
- Check whether timestamps are present and reliable.
- Make a data dictionary.

**Do not invent unobserved metrics or treat filename metadata as verified document properties.**

## 3. Python ingestion

Create separate ingestion scripts for document and issue exports when each is available. Steps:

1. Read Excel/CSV using pandas or another supported library.
2. Preserve the raw values and original columns.
3. Append `source_file`, `source_sheet`, `ingestion_timestamp` in an ingestion metadata layer.
4. Standardise dates, names, identifiers and missing-value handling in a separate clean layer.
5. Record rejected rows and validation failures.
6. Ensure repeated ingestion doesn't create duplicate facts.

## 4. SQL data model

Create only tables that available data can populate:

| Table | Grain / role | Condition |
|---|---|---|
| `raw_documents` | Exported file/document rows | Needs actual Files Log/export |
| `raw_issues` | Issue rows | Needs issue workbook/export |
| `fact_documents` | One document per agreed business key | If document fields support it |
| `fact_document_versions` | One document version | Only with version-level source data |
| `fact_issues` | One issue | After verifying unique issue key |
| `fact_reviews` | One review event | Only if review history is exported |
| `dim_date` | Calendar | For available date fields |
| `dim_discipline` | Discipline lookup | If discipline values exist |
| `dim_status` | Status lookup | If status values exist |

Validate join keys and model grain. Avoid counting multiple versions as separate documents unless the metric explicitly asks for versions.

## 5. Reporting features and DAX

Possible measures, **only where supported by actual columns**:

- Total documents
- Total issues
- Open issues
- Closed issues
- Issues by status/category/assignee
- Documents by file type/discipline
- Document versions by period
- Resolution time if reliable open/close dates exist
- Overdue reviews if reviewer, due date and review state exist

Examples to adapt **after confirming schema**:

```dax
Total Issues = COUNTROWS(fact_issues)

Open Issues =
CALCULATE(
    [Total Issues],
    fact_issues[status] = "Open"
)

Open Issue Rate = DIVIDE([Open Issues], [Total Issues])
```

These formulas are templates. Status labels must match the real exported data.

## 6. Power BI dashboard plan

### Dashboard 1 — Executive overview

- Total documents (if available)
- Total issues
- Open/closed breakdown
- Counts over time when timestamps exist
- Key filters by category/discipline

### Dashboard 2 — Document control

- Files by document type and discipline
- Document register with metadata
- Version activity if exported
- Review/approval metrics only if corresponding records exist

### Dashboard 3 — Issue management

- Issue status composition
- Issue category/assignee/location
- Trends based on actual available timestamps
- Detailed issue drill-through

### Dashboard 4 — Searchable project register

- Detailed issue and/or document table
- Search and slicers
- Links or identifiers for source traceability
- Data refresh timestamp

## 7. Validation before publishing

- Compare exported/source row counts to ingested raw tables.
- Reconcile unique issue and document counts.
- Detect duplicates introduced by relationships.
- Verify null/date handling.
- Cross-check Power BI totals against SQL queries.
- Test slicers and relationships.
- Report data limitations prominently.

## 8. Next iteration: APS integration

Once manual exports work reliably, investigate Autodesk Platform Services APIs for the same records. Implement:

- Authentication and token refresh
- Pagination
- Rate limiting and retry logic
- Incremental updates
- Schema change monitoring
- Permissions and secrets handling
- Logging and reconciliation

Keep the demo clearly labelled as a real API integration only if you successfully access and process data from that API.

## 9. Portfolio story

Document the full chain:

**Sample project → File/issue management → Authorised export → Python ingestion → Validation → SQL model → Power BI → QA.**

Include screenshots, table designs, quality checks, lessons learned and limitations. Do not merge or misattribute this sample project's data to the separate USACE procurement RFI register.
