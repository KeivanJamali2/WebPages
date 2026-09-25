# Project Instructions

## Project Context

This is an existing Flask website that has been developed and used for several months.

The application analyzes data and uses a SQLite database.

This is an established working system. Existing functionality is important and must be preserved.

The current major task involves incorporating newly available data into the existing website.

## Existing Application

Before modifying anything:

1. Inspect the existing application structure.
2. Understand how the relevant functionality currently works.
3. Understand the existing SQLite database and schema before making database changes.
4. Identify existing patterns, utilities, routes, models, queries, templates, and frontend components that should be reused.

## Database Safety

The SQLite database contains existing application data.

Never:
- Delete the database.
- Recreate the database from scratch.
- Reset or clear existing data.
- Drop tables unless explicitly instructed.
- Modify existing schema without first explaining the impact.

When database changes are required, inspect the current schema first and preserve existing data.

## Python Environment

Use the Conda environment:

`web-python`

Do not install packages automatically. I prefer to install them myself.

## Investigation Before Changes

For the initial investigation of this project, do not modify files or the database.

First understand the existing system and report:

- Application structure
- Flask entry point
- Main routes
- Database location and schema
- Data flow
- Important Python modules
- Templates/frontend structure
- Existing configuration
- How the application is currently run
- Relevant dependencies
- Anything that may be affected by the new data

## Testing

After meaningful changes:

- Run relevant tests or validation.
- If no tests exist, perform the most appropriate available validation.
- Report exactly what was tested.

Do not claim that something works unless it has actually been checked.

## Safety

Do not make destructive or difficult-to-reverse changes without explaining them first.

Never expose secrets, API keys, passwords, tokens, or credentials.

## Application Reference (from initial investigation)

The repo contains several historical iterations (`V0` -> `V4`). **`V4/` is the current live application** — it has the active SQLite database, the most complete templates, and recent upload/log activity. Earlier versions (`V0`-`V3`) are prior iterations kept for history only; `V3/Website` was the last CSV-file-based version before the move to SQLite. Always work in `V4/` unless told otherwise.

### Running the app

- Conda env: `web-python` (already has all packages from `V4/requirements.txt` installed).
- Run: `cd V4 && conda activate web-python && python app.py` — serves at `http://localhost:5000`.
- `DEBUG = True` in `V4/config.py`. No `.env` file in `V4` (no secrets on disk there).
- Login is a flat file `V4/users.txt` (`username,password,phone`, **plaintext**, no public signup).

### Entry point & routes

- Entry point: `V4/app.py` (~2240 lines).
- Auth/session routes: `/login`, `/logout`, `/dashboard`.
- Data ingestion: `/upload` (ZIP, max 500MB) -> `/process_data` (runs `cleaner.StoreData`) -> duplicate check -> `/duplicates` (resolve via `DuplicateDetector`).
- Database admin: `/manage_database`, `/clear_database` (full wipe — destructive, only via explicit user action in the UI).
- Analysis: `/analyze` (runs `analyzer.SQLiteAnalyzer`, driven by `V4/available_analyses.txt`, 14 analysis types) -> `/plots`, `/downloads`.
- JSON API (`/api/*`): browse/search by date, reference code, field, employee; duplicate handling; "no workflow" request listing + manual workflow editing (`get_requests_with_no_workflow`, `apply_workflow_text`); raw-template transform (`template_transformer.py`); file preview + message-flow graph view.

### Database

- Location: `V4/database/hami.db` (SQLite). DB helper class: `HamiDatabase` in `V4/database.py`.
- Two tables:
  - **`requests`**: one row per Hami support "request" — `id, hami_id, number, subject, reference_code, major, name, national_id, student_id, field, first_date, last_date, created_at`.
  - **`messages`**: one row per message in a request — `id, request_id (FK -> requests.id, ON DELETE CASCADE), date, message, from_name, to_name, to_email, from_id, to_id, matched`.
- Indexes on `requests(hami_id, reference_code, name)` and `messages(request_id, date, from_name, to_name)`.
- **Known schema drift**: the live on-disk schema has `UNIQUE(hami_id, number, reference_code)` on `requests`, but `database.py`'s `_init_database()` (`CREATE TABLE IF NOT EXISTS`) defines `reference_code TEXT UNIQUE` instead — an older schema version is actually persisted, and `CREATE TABLE IF NOT EXISTS` never migrates it. **Do not trust `database.py`'s DDL as the source of truth — always check the live schema with `sqlite3 V4/database/hami.db ".schema"` first.** Any real schema change needs an explicit `ALTER TABLE` migration, never rely on the `_init_database` code path to change an existing DB.
- Dedup key: `reference_code`. New inserts that collide on it are caught and surfaced in `/duplicates` for manual resolution.
- As of the initial investigation: 4,979 requests, 23,042 messages, Jalali date range `1403-12-26` to `1404-09-21`, file size 13.8 MB.

### Data flow for new data (upload -> analysis)

1. ZIP upload, expected raw file naming: `file_i_j.txt` / `workflow_i_j.txt`.
2. `cleaner.RawDataReader` indexes extracted `.txt` files.
3. `cleaner.DataLoader` (`V4/cleaner.py:55-202`) parses one request's raw text — subject, reference code, major, student info, messages, workflow. **This is where to adapt parsing if a new data source has a different raw format.**
4. `cleaner.CombineData` merges message + workflow data per request.
5. `cleaner.StoreData.fit(i_values)` writes parsed requests/messages into SQLite via `HamiDatabase`, auto-assigning a per-hami sequential `number`.
6. `cleaner.DuplicateDetector` flags duplicate `reference_code`s post-import.
7. `analyzer.SQLiteAnalyzer` (`V4/analyzer.py`, class starts line 26) queries SQLite directly (no CSV loading) to produce plots (matplotlib/seaborn, Persian text via `arabic_reshaper`/`python-bidi`) and CSV exports.
8. `cleaner.LegacyCSVMigrator` exists for migrating older CSV-format data into SQLite — relevant if new data arrives in the old `V3` CSV format instead of raw ZIP/txt.

### Key modules (`V4/`)

- `app.py` — Flask routes (~2240 lines).
- `cleaner.py` — raw data parsing & SQLite ingestion: `RawDataReader`, `DataLoader`, `CombineData`, `StoreData`, `DuplicateDetector`, `LegacyCSVMigrator`.
- `analyzer.py` — analytics engine: `SQLiteAnalyzer` (current, queries DB directly), plus legacy `SQLiteDataLoader`/`DataLoader`/`DataAnalyzer` classes (CSV-based, likely superseded — verify before reusing).
- `database.py` — `HamiDatabase` (all SQLite access; see schema drift note above).
- `template_transformer.py` — normalizes raw/uncleaned pasted template text into workflow format.
- `config.py` — paths, upload limits, `available_analyses.txt`/`analysis_config.json` loaders.

### Frontend

- Bootstrap 5 + vanilla JS. Templates in `V4/templates/`: `base.html`, `login.html`, `dashboard.html`, `upload.html`, `process_data.html`, `manage_database.html` (largest — DB browse/search/dedup UI), `duplicates.html`, `duplicates_select.html`, `analyze.html`, `plots.html`, `downloads.html`, `help.html`, `404.html`, `500.html`.
- JS: `static/js/main.js`, `static/js/database_manager.js`.

### Dependencies

`V4/requirements.txt` pins: Flask 3.0.0, Werkzeug 3.0.1, pandas 2.1.4, numpy 1.26.2, jdatetime 4.1.0, matplotlib 3.8.2, seaborn 0.13.0, arabic-reshaper 3.0.0, python-bidi 0.4.2, openpyxl 3.1.2, python-dateutil 2.8.2. All confirmed installed in `web-python`, though some installed versions are newer than the pins (e.g. Flask 3.1.2, numpy 2.4.0) — not currently a blocker, but relevant if strict version parity ever matters.
