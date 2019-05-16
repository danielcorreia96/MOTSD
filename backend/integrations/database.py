# coding=utf-8
import pandas as pd
import pyodbc
from pathlib import Path
from joblib import Memory

database_home = "data\\database\\"
memory = Memory(Path(f"{database_home}"), verbose=0)
DB_CONFIG = Path(f"{database_home}database.config").read_text()


@memory.cache
def get_test_name_fails(max_date):
    print("Querying database for test name fails")
    query = Path(f"{database_home}test_name_fails.sql").read_text()
    connection = pyodbc.connect(DB_CONFIG)
    return pd.read_sql_query(query, connection, params=[max_date])


@memory.cache
def get_testfails_for_revision(revision):
    print(f"Querying db for test fails for rev {revision}")
    query = Path(f"{database_home}test_fails_rev.sql").read_text()
    connection = pyodbc.connect(DB_CONFIG)
    return pd.read_sql_query(query, connection, params=[revision])


@memory.cache
def get_test_execution_times():
    print(f"Querying db for test execution times")
    query = Path(f"{database_home}test_execution_times.sql").read_text()
    connection = pyodbc.connect(DB_CONFIG)
    return pd.read_sql(query, connection)
