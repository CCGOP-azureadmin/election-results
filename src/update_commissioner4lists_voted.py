import pyodbc
import json
import os

# Load SQL config
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
    # Set Voted=1 in Commissioner4Lists for each match in prim26_Voters
    update_sql = '''
    UPDATE Commissioner4Lists
    SET Voted = 1
    WHERE EXISTS (
        SELECT 1 FROM prim26_Voters v
        WHERE v.FirstName = Commissioner4Lists.FirstName
          AND v.LastName = Commissioner4Lists.LastName
          AND v.MiddleName = Commissioner4Lists.MiddleName
          AND v.Precinct = Commissioner4Lists.Precinct
          AND v.StreetName = LTRIM(RIGHT(Commissioner4Lists.Address, LEN(Commissioner4Lists.Address) - CHARINDEX(' ', Commissioner4Lists.Address)))
    )
    '''
    cursor.execute(update_sql)
    conn.commit()
    cursor.close()
    conn.close()
    print("Commissioner4Lists.Voted updated for all matching voters.")
