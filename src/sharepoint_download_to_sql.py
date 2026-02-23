from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Auto-load .env if present
dotenv_path = Path(__file__).parent.parent / '.env'
if load_dotenv and dotenv_path.exists():
    load_dotenv(dotenv_path)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import pyodbc
import json
from config.sharepoint_sync_config import SHAREPOINT_SITE_HOSTNAME, SHAREPOINT_SITE_PATH, SQL_TABLE
AZURE_TENANT_ID = os.environ.get('ENTRA_TENANT_ID')
AZURE_CLIENT_ID = os.environ.get('ENTRA_CLIENT_ID')
AZURE_CLIENT_SECRET = os.environ.get('ENTRA_CLIENT_SECRET')
# 1. Get Azure AD token for SharePoint

def get_access_token():
    # Fast-fail if any credential is missing
    if not AZURE_TENANT_ID or not AZURE_CLIENT_ID or not AZURE_CLIENT_SECRET:
        print("ERROR: One or more Azure AD credentials are missing. Check your .env or environment variables.")
        print(f"AZURE_TENANT_ID: {AZURE_TENANT_ID}")
        print(f"AZURE_CLIENT_ID: {AZURE_CLIENT_ID}")
        print(f"AZURE_CLIENT_SECRET: {'SET' if AZURE_CLIENT_SECRET else 'MISSING'}")
        exit(1)
    url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
    data = {
        'grant_type': 'client_credentials',
        'client_id': AZURE_CLIENT_ID,
        'client_secret': AZURE_CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default'
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()['access_token']

# 2. Get all lists matching <precinct num>_zone<zone num>

def get_sharepoint_lists(token):
    # Use Microsoft Graph API to get site id
    site_url = f"https://graph.microsoft.com/v1.0/sites/{SHAREPOINT_SITE_HOSTNAME}:{SHAREPOINT_SITE_PATH}:"
    headers = {'Authorization': f'Bearer {token}'}
    site_resp = requests.get(site_url, headers=headers)
    site_resp.raise_for_status()
    site_id = site_resp.json()['id']
    # Get lists from site
    lists_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"
    lists_resp = requests.get(lists_url, headers=headers)
    lists_resp.raise_for_status()
    lists = lists_resp.json()['value']
    # Return only lists matching zone pattern (e.g., '40-zone11')
    import re
    return [lst for lst in lists if re.match(r'^\d+-zone\d+$', lst['displayName'])]

# 3. Download all items from each list

def get_list_items(token, list_title):
    url = f"https://{SHAREPOINT_SITE_HOSTNAME}{SHAREPOINT_SITE_PATH}/_api/web/lists/getbytitle('{list_title}')/items?$top=5000"
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json;odata=verbose'}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()['d']['results']

# 4. Insert into SQL

def insert_to_sql(all_rows, columns):
    config_path = os.path.join(os.path.dirname(__file__), '../config/sql_config.json')
    with open(config_path, 'r') as f:
        cfg = json.load(f)
    conn_str = (
        f"DRIVER={cfg['driver']};"
        f"SERVER={cfg['server']};"
        f"DATABASE={cfg['database']};"
        f"Trusted_Connection={cfg.get('trusted_connection', 'yes')};"
        f"TrustServerCertificate={cfg.get('TrustServerCertificate', 'yes')}"
    )
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    col_defs = ', '.join([f'[{col}] VARCHAR(255)' for col in columns])
    cursor.execute(f"IF OBJECT_ID('{SQL_TABLE}', 'U') IS NOT NULL DROP TABLE [{SQL_TABLE}]; CREATE TABLE [{SQL_TABLE}] ({col_defs})")
    placeholders = ','.join(['?' for _ in columns])
    for row in all_rows:
        values = [row.get(col, '') for col in columns]
        cursor.execute(f"INSERT INTO {SQL_TABLE} ({','.join(columns)}) VALUES ({placeholders})", values)
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    token = get_access_token()
    lists = get_sharepoint_lists(token)
    all_rows = []
    columns = set()
    if lists:
        all_rows = []
        columns = set()
        headers = {'Authorization': f'Bearer {token}'}
        for lst in lists:
            list_id = lst['id']
            items_url = f"https://graph.microsoft.com/v1.0/sites/{SHAREPOINT_SITE_HOSTNAME}:{SHAREPOINT_SITE_PATH}:/lists/{list_id}/items?$top=5000&$expand=fields"
            items_resp = requests.get(items_url, headers=headers)
            items_resp.raise_for_status()
            items = items_resp.json()['value']
            precinct = ''
            zone = ''
            m = __import__('re').match(r'^(\d+)-zone(\d+)$', lst['displayName'])
            if m:
                precinct = m.group(1)
                zone = m.group(2)
            for item in items:
                sp_fields = item.get('fields', {})
                print("DEBUG: SharePoint item fields:", sp_fields)
                row = {
                    'Site': 'Commissioner4',
                    'ListName': lst['displayName'],
                    'Voted': 'FALSE',
                    'Zone': zone,
                    'Precinct': precinct,
                    'FirstName': sp_fields.get('Firstname', ''),
                    'LastName': sp_fields.get('Lastname', ''),
                    'MiddleName': sp_fields.get('Middlename', ''),
                    'Address': sp_fields.get('Address', '')
                }
                all_rows.append(row)
        if all_rows:
            columns = list(all_rows[0].keys())
        else:
            columns = []
        insert_to_sql(all_rows, columns)
        print(f"Downloaded {len(all_rows)} items from {len(lists)} lists into {SQL_TABLE}")
    else:
        print("No lists found.")
