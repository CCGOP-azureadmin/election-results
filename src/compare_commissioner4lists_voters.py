import pyodbc
import json
import os

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

if __name__ == "__main__":
    cfg = load_sql_config()
    conn = get_sql_connection(cfg)
    cursor = conn.cursor()
    # Show sample rows from both tables for join fields
    print('Sample from Commissioner4Lists:')
    cursor.execute('SELECT TOP 5 FirstName, LastName, MiddleName, Address, Precinct FROM Commissioner4Lists')
    for row in cursor.fetchall():
        print(row)
    print('\nSample from prim26_Voters:')
    cursor.execute('SELECT TOP 5 FirstName, LastName, MiddleName, StreetName, Precinct FROM prim26_Voters')
    for row in cursor.fetchall():
        print(row)
    cursor.close()
    conn.close()
