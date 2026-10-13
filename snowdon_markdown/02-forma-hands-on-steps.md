# Snowdon Towers: Forma Data Management Hands-on Guide

## Step 1. Inspect the sample project

1. Open **Construction: Sample Project – Snowdon Towers**.
2. Enter **Data Management → Files**.
3. Inspect **Project Files** and existing Autodesk sample folders.
4. Confirm which actions your account can perform: create folder, upload, manage attributes, inspect versions, review, issues, export.
5. Avoid deleting or altering original sample content.

## Step 2. Create a separate learning workspace

If your permissions allow, create:

```text
Project Files/
└── Digital Engineering Practice/
    ├── 01_Design Files/
    ├── 02_Drawings/
    ├── 03_Models/
    ├── 04_Reports/
    └── 05_Contracts/
```

These are document-type categories, **not** a literal ISO 19650 state structure.

## Step 3. Upload the documents

Upload through the browser's Files interface:

- `01_Design Files`: `S102-Main Level.pdf`, `S103-Second Level.pdf`, `S107-Roof.pdf`, `S108-Stair Towers.pdf`, `S600-Details.pdf`, `Snowdon Towers Sample Structural - Multipage.pdf`.
- `02_Drawings`: 5 `.dwg` files.
- `03_Models`: `Snowdon Towers Sample Structural.rvt`.
- `04_Reports`: `Snowden Towers Sample Issue Summary.xlsx`.
- `05_Contracts`: `Executed Subcontract Agreement – Structural Steel Fabrication & Erection_0.docx`.

After uploading each category, verify the files are present and preview them where supported. Capture screenshots for your case study. The local inventory alone is **not** proof of upload.

## Step 4. Investigate document metadata

For each document, record available fields such as:

- File/document identifier
- Title and type
- Discipline
- Upload date and uploader
- Version, revision (if known), suitability (if known)
- Folder and any access restrictions
- Review status (only if actual review exists)

Example practice document register (illustrative identifiers):


| Practice ID | File                  | Type | Discipline | Revision              |
| ----------- | --------------------- | ---- | ---------- | --------------------- |
| ST-S-102    | S102-Main Level.pdf   | PDF  | Structural | Unknown until checked |
| ST-S-103    | S103-Second Level.pdf | PDF  | Structural | Unknown until checked |
| ST-S-107    | S107-Roof.pdf         | PDF  | Structural | Unknown until checked |
| ST-S-108    | S108-Stair Towers.pdf | PDF  | Structural | Unknown until checked |
| ST-S-600    | S600-Details.pdf      | PDF  | Structural | Unknown until checked |




## Step 5. Explore versions, reviews and issues

Use `S102-Main Level.pdf` in the **practice folder** for a controlled exercise:

1. Open file details and inspect available version history.
2. Inspect review/approval options, if included in the account.
3. Draft a clearly labelled **practice** review scenario with a comment and owner.
4. If permitted, create a revised practice copy and inspect how versions are handled.
5. Record results and screenshots; distinguish actual platform actions from manual/simulated activities.

Do **not** represent a practice review as genuine engineering approval. Do not assume the sample account allows all workflows.

## Step 6. Inspect the issue summary

Open `Snowden Towers Sample Issue Summary.xlsx` locally and determine:

- Worksheets and row counts
- Issue identifier or unique key
- Status and category fields
- Assignment/owner fields
- Created and closed dates, if provided
- Location and discipline, if provided
- Missing/duplicate identifiers

Do not calculate overdue reviews or resolution time unless the source contains the dates and definitions needed.

## Step 7. Identify export paths



### Manual export first

Look for available Files Log/document list and issue export functions in the project. Export to CSV/Excel when supported and retain the original export unchanged.

### API extension, optional

Study Autodesk Platform Services project discovery, authentication, Data Management APIs and supported issue endpoints. Validate permissions and scope before attempting an integration.

## First session checklist

- [ ] Open Snowdon Towers in Data Management.
- [ ] Inspect Project Files and permissions.
- [ ] Create Digital Engineering Practice folder (if allowed).
- [ ] Create five subfolders.
- [ ] Upload `S102-Main Level.pdf`.
- [ ] Preview it and capture its file details.
- [ ] Check version and review options.
- [ ] Inventory `Snowden Towers Sample Issue Summary.xlsx`.



## What to document

Record **what you did**, **what the platform actually supported**, **what required simulation**, **what data you obtained**, and **what you learned**. This distinction makes the portfolio honest and credible.