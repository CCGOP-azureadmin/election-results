# CSV-SQL Workspace

This project is for processing CSV files and integrating with SQL Server using Python.

## Features
- CSV parsing and transformation
- SQL Server integration (read/write)
- Unit tests with pytest

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
2. Activate the environment:
   - Windows: `.venv\Scripts\activate`
   - Mac/Linux: `source .venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
- Place your CSV files in the `data/` folder.
- Configure SQL Server connection in `config/sql_config.json`.
- Run scripts from the `src/` folder.

## Testing
- Run tests with:
   ```bash
   pytest
   ```

## Requirements
- Python 3.8+
- SQL Server

## Dependencies
- pandas
- pyodbc
- pytest

---
Replace sample files and configs with your actual data and credentials.
