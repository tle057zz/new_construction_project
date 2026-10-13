-- Tables this workbook can fill.
-- One issue row per exported ID, one fact per ID, and lookups for status, category, and type.
-- No discipline, document, version, review, or calendar table.

CREATE TABLE overview (
    excel_cell TEXT NOT NULL,
    value TEXT,
    value_kind TEXT NOT NULL,
    source_file TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    ingestion_timestamp TEXT NOT NULL
);

CREATE TABLE issue_rows (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    category TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    assigned_to TEXT NOT NULL,
    company TEXT NOT NULL,
    watchers TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_on TEXT NOT NULL,
    due_date TEXT,
    start_date TEXT,
    location TEXT,
    location_details TEXT,
    placement TEXT,
    root_cause TEXT,
    published TEXT NOT NULL,
    updated_by TEXT,
    updated_on TEXT NOT NULL,
    closed_by TEXT,
    closed_at TEXT,
    comments TEXT,
    additional_comments TEXT,
    areas_affected TEXT,
    building_element TEXT,
    cost_impact TEXT,
    date_received TEXT,
    defect TEXT,
    linked_asset TEXT,
    facilities_team_review_status TEXT,
    hyperlink_1 TEXT,
    hyperlink_2 TEXT,
    install_date TEXT,
    interface_topic TEXT,
    lessons_learned_candidate TEXT,
    multi_select_dropdown TEXT,
    numeric_field TEXT,
    part_number TEXT,
    project_task_code TEXT,
    quality_issue_with_cost TEXT,
    review_status TEXT,
    risk_level TEXT,
    row_label TEXT,
    sc_acknowledged TEXT,
    seat TEXT,
    serial_number_1 TEXT,
    serial_number_2 TEXT,
    ship_date TEXT,
    size_text TEXT,
    warranty_info TEXT,
    warranty_number TEXT,
    work_order_number TEXT,
    source_file TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    ingestion_timestamp TEXT NOT NULL
);

CREATE TABLE dim_status (
    status_id INTEGER PRIMARY KEY,
    status TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_category (
    category_id INTEGER PRIMARY KEY,
    category TEXT NOT NULL UNIQUE
);

CREATE TABLE dim_type (
    type_id INTEGER PRIMARY KEY,
    type TEXT NOT NULL UNIQUE
);

CREATE TABLE fact_issues (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status_id INTEGER NOT NULL REFERENCES dim_status (status_id),
    category_id INTEGER NOT NULL REFERENCES dim_category (category_id),
    type_id INTEGER NOT NULL REFERENCES dim_type (type_id),
    assigned_to TEXT NOT NULL,
    company TEXT NOT NULL,
    created_on TEXT NOT NULL,
    due_date TEXT,
    start_date TEXT,
    updated_on TEXT NOT NULL,
    closed_at TEXT,
    location TEXT,
    published TEXT NOT NULL,
    source_file TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    ingestion_timestamp TEXT NOT NULL
);
