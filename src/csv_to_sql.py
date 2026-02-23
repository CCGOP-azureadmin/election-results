

import pandas as pd
import pyodbc
import json
import os
import re

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/sql_config.json')

def load_sql_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def get_sql_connection(cfg):
    conn_str = (
        f"DRIVER={cfg['driver']};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"Trusted_Connection={cfg.get('trusted_connection', 'yes')};"
        f"TrustServerCertificate={cfg.get('TrustServerCertificate', 'yes')}"
    )
    return pyodbc.connect(conn_str)

def map_row(row):
    # Parse Voter Name
    # Determine if this is an absentee file (VUID column) or early vote (CertificateNumber)
    is_absentee = 'VUID' in row.index
    if is_absentee:
        # Absentee mapping
        mapped = {
            'LastName': row.get('Last Name', ''),
            'FirstName': row.get('First Name', ''),
            'MiddleName': row.get('Middle Name', ''),
            'StreetName': '',
            'City': '',
            'Zip': '',
            'SOSVoterId': row.get('VUID', ''),
            'Party': row.get('_Party', ''),
            'VoteType': 'Absentee',
            'VotedPhase': 'Absentee',
            'VotedBallotStyle1': ''
        }
        for col in row.index:
            if col not in ['Last Name', 'First Name', 'Middle Name', 'VUID', '_Party']:
                mapped[col] = row.get(col, '')
        return mapped
    # Early vote mapping
    voter_name = row.get('VoterName', '') or row.get('Voter Name', '')
    last_name, first_name, middle_name = '', '', ''
    if voter_name and ',' in voter_name:
        name_split = voter_name.split(',', 1)
        last_name = name_split[0].strip()
        first_middle = name_split[1].strip()
        first_middle_split = first_middle.split(' ', 1)
        first_name = first_middle_split[0] if len(first_middle_split) > 0 else ''
        middle_name = first_middle_split[1] if len(first_middle_split) > 1 else ''
    voter_address = row.get('VoterAddress', '') or row.get('Voter Address', '')
    street_name, city, zip_code = '', '', ''
    if isinstance(voter_address, str) and voter_address:
        address_split = [x.strip() for x in voter_address.split(',')]
        if len(address_split) >= 3:
            street_name = address_split[0]
            city = address_split[1]
            zip_match = re.search(r'\b\d{5}(?:-\d{4})?\b', address_split[2])
            zip_code = zip_match.group(0) if zip_match else ''
    mapped = {
        'LastName': last_name,
        'FirstName': first_name,
        'MiddleName': middle_name,
        'StreetName': street_name,
        'City': city,
        'Zip': zip_code,
        'SOSVoterId': row.get('CertificateNumber', ''),
    }
    for col in row.index:
        if col not in ['Voter Name', 'VoterName', 'Voter Address', 'VoterAddress', 'Certificate Number', 'CertificateNumber']:
            mapped[col] = row.get(col, '')
    return mapped

def create_table(cursor, table_name, sample_record):
    columns = ',\n    '.join([f"[{k}] VARCHAR(255)" for k in sample_record.keys()])
    sql = f"""
    IF OBJECT_ID(N'{table_name}', N'U') IS NOT NULL DROP TABLE [{table_name}];
    CREATE TABLE [{table_name}] (
    {columns}
    );
    """
    cursor.execute(sql)

def process_csvs_to_sql(csv_paths, table_name):
    cfg = load_sql_config()
    conn = get_sql_connection(cfg)
    cursor = conn.cursor()
    all_records = []
    for csv_path in csv_paths:
        df = pd.read_csv(csv_path, dtype=str)
        for _, row in df.iterrows():
            mapped = map_row(row)
            all_records.append(mapped)
    if not all_records:
        print("No records to insert.")
        return
    # Create table
    create_table(cursor, table_name, all_records[0])
    # Insert records
    columns = list(all_records[0].keys())
    placeholders = ','.join(['?' for _ in columns])
    insert_sql = f"INSERT INTO [{table_name}] (" + ','.join(f'[{c}]' for c in columns) + f") VALUES ({placeholders})"
    import math
    for rec in all_records:
        values = [str(rec.get(col, '') or '') if not (isinstance(rec.get(col, ''), float) and math.isnan(rec.get(col, ''))) else '' for col in columns]
        cursor.execute(insert_sql, values)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Uploaded {len(all_records)} rows to {table_name}")

if __name__ == "__main__":
    base_path = r"C:/Users/frank/OneDrive - Clarity Data Services/2026 Primary"
    files = [
        ("Early Voters Through February 22, 2026 REP.csv", "REP"),
        ("Early Voters Through February 22, 2026 DEM.csv", "DEM"),
    ]
    csv_paths = []
    for fname, party in files:
        fpath = os.path.join(base_path, fname)
        csv_paths.append(fpath)
    # Clear the table before inserting new rows
    cfg = load_sql_config()
    conn = get_sql_connection(cfg)
    cursor = conn.cursor()
    cursor.execute("IF OBJECT_ID('prim26_Voters', 'U') IS NOT NULL DROP TABLE [prim26_Voters];")
    conn.commit()
    cursor.close()
    conn.close()
    process_csvs_to_sql(csv_paths, 'prim26_Voters')
