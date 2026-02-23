import pandas as pd
from src.csv_to_sql import load_sql_config

def test_load_sql_config():
    cfg = load_sql_config()
    assert 'server' in cfg
    assert 'database' in cfg
    assert 'username' in cfg
    assert 'password' in cfg
    assert 'driver' in cfg

# Add more tests for CSV processing and SQL integration as needed
