# coding=utf-8
import pandas as pd
import pyodbc
from pathlib import Path
from joblib import Memory

database_home = "data\\database\\"
memory = Memory(Path(f"{database_home}"), verbose=0)
DB_CONFIG = Path(f"{database_home}database.config").read_text()


@memory.cache
def get_test_name_fails(start_date: str, max_date: str) -> pd.DataFrame:
    """
    Query the database for the number of test fails on a given date interval.

    :param start_date: start date
    :param max_date: maximum date
    :return: 2-columns dataframe with the tests names and number of fails
    """
    print("Querying database for test name fails")
    query = Path(f"{database_home}test_name_fails.sql").read_text()
    connection = pyodbc.connect(DB_CONFIG)
    return pd.read_sql_query(query, connection, params=[start_date, max_date])


@memory.cache
def get_testfails_for_revision(revision: str) -> pd.DataFrame:
    """
    Query the database for the tests that failed on a given revision.

    :param revision: revision id
    :return: 1-column dataframe with the test names
    """
    print(f"Querying db for test fails for rev {revision}")
    query = Path(f"{database_home}test_fails_rev.sql").read_text()
    connection = pyodbc.connect(DB_CONFIG)
    return pd.read_sql_query(query, connection, params=[revision])


@memory.cache
def has_missing_builds_for_revision(revision: str) -> bool:
    """
    Check in database if a given revision has missing builds of one of the stages.

    :param revision: revision id
    :return: True if the revision has missing builds
    """
    print(f"Querying db for missing builds for rev {revision}")
    for stage in ["nodevbuild", "nocorebuild"]:
        query = Path(f"{database_home}check_{stage}_rev.sql").read_text()
        connection = pyodbc.connect(DB_CONFIG)
        result = pd.read_sql_query(query, connection, params=[revision])
        if len(set(result.FULLNAME.values)) == 0:
            print(f"Missing builds for {stage}")
            return True
    return False


@memory.cache
def get_test_execution_times(from_dt: str, to_dt: str) -> pd.DataFrame:
    """
    Query the database for the test execution times on a given date interval.

    :param from_dt: start date
    :param to_dt: end date
    :return: 2-columns dataframe with the tests names and test execution times
    """
    print(f"Querying db for test execution times")
    query = Path(f"{database_home}test_execution_times.sql").read_text()
    connection = pyodbc.connect(DB_CONFIG)
    return pd.read_sql_query(query, connection, params=[from_dt, to_dt])
