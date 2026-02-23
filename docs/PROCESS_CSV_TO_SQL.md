# Process: CSV -> SQL (Daily)

This document explains how to run the daily CSV ingestion that loads election CSVs into the `prim26_Voters` SQL table.

Prerequisites
- Windows machine with access to the OneDrive folder containing CSVs: `C:\Users\frank\OneDrive - Clarity Data Services\2026 Primary`
- Python virtual environment created and activated in the repo root: `.venv`
- Python dependencies installed via `requirements.txt` (pandas, pyodbc, pytest)
- SQL Server reachable from your machine and credentials configured in `config/sql_config.json`

Files involved
- `src/csv_to_sql.py` — main script. Reads configured CSV file names from the script's `files` list, maps columns, drops/creates `prim26_Voters` and inserts rows.
- `config/sql_config.json` — SQL connection configuration used by the script.
- CSVs — e.g. `Early Voters Through <date> DEM.csv` and `Early Voters Through <date> REP.csv` in the OneDrive folder.

What the script does
1. Reads the CSV files listed in the `files` list inside `src/csv_to_sql.py`.
2. Maps each row into a normalized dictionary (handles absentee vs early vote formats).
3. Drops `prim26_Voters` table if it exists and creates a new table based on the mapped columns.
4. Inserts all rows into `prim26_Voters`.

How to run (safe, repeatable steps)
1. Open PowerShell and change to the repository root:

```powershell
cd C:\Development\Clarity\election-results
.venv\Scripts\Activate.ps1
```

2. (Only if not already done) Install dependencies:

```powershell
.venv\Scripts\pip.exe install -r requirements.txt
```

3. Verify `config/sql_config.json` contains correct connection settings (driver, server, database, Trusted_Connection). Do NOT commit credentials into source control.

4. Update the `files` list in `src/csv_to_sql.py` if the filenames differ from the hard-coded entries. The script currently contains a hard-coded list of CSV filenames; update to the desired date filenames or modify the script to wildcard-match.

5. Run the ingestion using the venv Python to ensure correct packages are used:

```powershell
.venv\Scripts\python.exe src\csv_to_sql.py
```

6. Observe console output for the number of rows uploaded. Example: `Uploaded 24857 rows to prim26_Voters`.

Notes and recommendations
- The script currently drops and recreates `prim26_Voters` on each run. If you need incremental loads, update `create_table` and insertion logic to `append` instead of `drop`.
- Consider automating the filename selection: replace the hard-coded `files` list with a pattern search (e.g., glob) to pick the latest `Early Voters` files.
- Ensure `config/sql_config.json` is never committed with production credentials. Use environment variables or a secrets store for production runs.
- Keep local OneDrive sync running so files are available at the configured path.

Troubleshooting
- `ModuleNotFoundError: No module named 'pandas'` — ensure you run the script with the venv python and that `pip install -r requirements.txt` completed successfully.
- `pyodbc` connection errors — verify the ODBC driver is installed and `sql_config.json` values are correct.

Change log
- 2026-02-19: Initial doc created after running `src/csv_to_sql.py` for Feb 19 CSVs.
