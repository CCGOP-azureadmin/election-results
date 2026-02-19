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
    # Check how many rows have Voted=1
    cursor.execute('SELECT COUNT(*) FROM Commissioner4Lists WHERE Voted=1')
    voted_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM Commissioner4Lists')
    total_count = cursor.fetchone()[0]
    print(f"Rows with Voted=1: {voted_count} / {total_count}")
    # Optionally, show a few sample rows
    cursor.execute('SELECT TOP 5 * FROM Commissioner4Lists WHERE Voted=1')
    for row in cursor.fetchall():
        print(row)
    cursor.close()
    conn.close()
