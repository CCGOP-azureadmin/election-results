# CSV -> SQL Processing: Repository Overview and Runbook

This document describes the purpose of the repository, the CSV -> SQL processing workflow used for the 2026 primary voter data, how the code works, and how to run it reproducibly.

## Purpose
- Store and process daily election CSV exports (Early Voters / Absentee) and load them into a SQL Server table for analysis.

## Key files
- `src/csv_to_sql.py` — main processing script. Reads configured CSVs, maps columns to a consistent schema, drops and recreates the `prim26_Voters` table, and inserts all rows.
- `src/sharepoint_download_to_sql.py` — helper for downloading/sharepoint sources (see file for details).
- `config/sql_config.json` — SQL connection configuration used by `csv_to_sql.py` (driver, server, database, trusted connection). Keep this file updated with correct credentials/connection info.
- `requirements.txt` — Python dependencies (`pandas`, `pyodbc`, `pytest`).
- `sql/` — SQL utilities and queries (e.g., `get_precinct_turnout.sql`).

## How the processing script works (high level)
1. `csv_to_sql.py` defines `map_row()` which normalizes either absentee or early-voter CSV rows into a consistent dictionary of columns.
2. `process_csvs_to_sql()` reads a list of CSV paths, maps rows, creates (drops/recreates) the `prim26_Voters` table using the first row as a sample schema, and inserts all mapped rows via `pyodbc`.
3. The script's main section currently points to the OneDrive folder base path and a pair of filenames. Before running, confirm those filenames match the files present in the OneDrive folder.

## Safety notes
- The script drops `prim26_Voters` before inserting. If you need to preserve previous data, back it up first (e.g., `SELECT * INTO prim26_Voters_backup_YYYYMMDD FROM prim26_Voters`).
- Ensure `config/sql_config.json` points to the correct SQL instance and the account has permission to create/drop tables and insert data.

## Running the workflow (recommended steps)
1. Activate the project's virtual environment (PowerShell):

```powershell
& .\.venv\\Scripts\\Activate.ps1
```

2. (Optional) Install dependencies if not already installed:

```powershell
.venv\\Scripts\\pip.exe install -r requirements.txt
```

3. Confirm the CSV filenames in `src/csv_to_sql.py` main block match the files in:

```
C:/Users/frank/OneDrive - Clarity Data Services/2026 Primary
```

4. Run the script using the venv Python to ensure correct packages are used:

```powershell
.venv\\Scripts\\python.exe src\\csv_to_sql.py
```

5. The script prints an upload summary like `Uploaded N rows to prim26_Voters` on success.

## Making ingestion automatic / improvements
- Make `src/csv_to_sql.py` search the base path for the newest matching `Early Voters` CSVs instead of hard-coded filenames, to avoid editing the script each day.
- Add logging and a backup step before the `DROP TABLE` to keep historical data.
- Add a small CLI or environment-variable configuration for the base path and date so ops staff can run without editing code.

## Troubleshooting
- `ModuleNotFoundError: No module named 'pandas'` — ensure you run the script with the virtualenv Python or install dependencies into the active environment.
- `FileNotFoundError` for CSV paths — confirm filenames in the OneDrive folder and update the `files` list in `src/csv_to_sql.py`.
- Connection errors — verify `config/sql_config.json` and that the machine/network can reach the SQL Server.

## Useful commands
- List git status and push:

```powershell
git status
git add docs/PROCESS.md
git commit -m "Add PROCESS.md documenting CSV->SQL workflow"
git push origin master
```

## Contact / Owner
- Owner: Frank (repository maintainer). For credential or SQL questions, contact the DB admin.

---
Place this file under `docs/` so it is available to anyone operating the pipeline.
