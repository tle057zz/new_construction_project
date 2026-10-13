# Snowdon Towers: Autodesk Forma → CDE/EDMS → Python → SQL → Power BI

## Where we are now

**Current stage: beginning of CDE implementation (approximately steps −7 to −5 of the original illustrative roadmap).**

Evidence provided:
- The Autodesk Forma screenshot shows access to **Construction: Sample Project – Snowdon Towers**, with **Data Management** shown as default access.
- The local `Project Files` directory includes **14 source files**, organised across five folders.
- This does **not** confirm that files have been uploaded to Forma or that review, issue, or export features are enabled.

### Local data inventory

| Folder | Contents | Intended use |
|---|---|---|
| `01_Design Files` | 5 individual PDF drawings; 1 multipage structural PDF | Document upload, review, metadata |
| `02_Drawings` | 5 DWG files | Drawing document control and coordination |
| `03_Models` | 1 RVT structural model | BIM viewing and model workflows |
| `04_Reports` | 1 Excel issue summary | Issue-data analytics |
| `05_Contracts` | 1 DOCX subcontract agreement | Document classification and access controls |

## Important separation from the original RFI project

The original **Digital Engineering RFI Analytics & AI Platform** uses a public **USACE procurement-stage RFI workbook**. Its original internal document management system is **unverified**. Autodesk Forma was described in that project as an **illustrative** upstream CDE, not a proven source. The **Snowdon Towers** project is a **separate hands-on CDE practice project**. Do not claim its drawings produced the USACE RFIs.

## End-to-end roadmap

| Step | Work | Deliverable |
|---|---|---|
| 1 | Configure Forma project and practice area | Folder structure and permissions understanding |
| 2 | Upload sample files | Managed PDFs, DWGs, RVT, Excel and DOCX |
| 3 | Add or capture document metadata | Document register |
| 4 | Practise versions and revisions | Document history |
| 5 | Explore reviews and approvals | Review workflow and evidence, if enabled |
| 6 | Explore issues | Issue records and issue summary |
| 7 | Export data using available functions | Source CSV/Excel files |
| 8 | Ingest exports with Python | Raw source tables with lineage |
| 9 | Clean and validate with SQL/Python | Validated data tables |
| 10 | Derive analytics features | Status and ageing measures where supported |
| 11 | Build a reporting model | Fact and dimension tables |
| 12 | Develop Power BI reports | Executive, document and issue pages |
| 13 | Reconcile and validate | QA and reconciliation report |
| 14 | Document solution and limitations | Portfolio case study |

## CDE concepts to demonstrate

- CDE: governed processes and tools to manage and exchange project information.
- EDMS: functions for document registration, metadata, versions, reviews, distribution, and audit history.
- ISO 19650 information states: **Work in Progress, Shared, Published, Archived**. These are **information states**, not necessarily four folders.
- Distinguish **file type folders** from **information states**.
- Distinguish **uploaded file version** from **formally designated drawing revision** and **suitability status**.
- Do not invent approvals, issue dates, formal revision codes, or responsibility assignments absent from the actual files.

## Success criteria

At the end, explain and demonstrate:
1. How a construction project is organised in Autodesk Forma Data Management.
2. How documents and their metadata are controlled.
3. How reviews, versions and issues are managed, within available access.
4. How authorised exports or APIs feed a traceable data pipeline.
5. How data quality is checked before reporting.
6. How Power BI presents action-oriented construction management information.

## Interview positioning

> I used Autodesk Forma's Snowdon Towers sample project to practise construction document management, and built a separate data processing and reporting pipeline around available sample exports. I distinguished real platform actions from simulated workflows, validated the data, and documented where the trial environment limited functionality.

Only use this statement after completing the activities it describes.
