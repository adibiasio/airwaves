"""Common functions relating to the db
"""

import sqlite3 as sql
import time

import pandas as pd

path_to_db = "/mnt/l/monitor.db"

def exists_in_db(col, table, value=None, path=path_to_db) -> bool:
    """Confirm specified value exists in the db

    @param[in] col - name of column to load
    @param[in] table - name of table to load
    @param[in] value - value to check
    @param[in] path - path to database
    @return Bool
    """
    connection = sql.connect(path)
    c = connection.cursor()

    if value:
        c.execute(f"SELECT * FROM {table} WHERE {col} = {value}")
        condition = c.fetchone()
    else:
        c.execute(f"SELECT * FROM {table}")
        names = [description[0] for description in c.description]
        condition = True if col in names else False

    if condition:
        return True
    else:
        print("Invalid Arguments: Argument does not exist")
        return False


def load(query, path=path_to_db) -> pd.DataFrame:
    """Converts sqlite3 db to pandas df

    @param[in] query - str with direct sql query (for more complex queries)
    @param[in] path - path to database
    @return df - pandas data frame with specified table and conditions
    """
    connection = sql.connect(path)
    c = connection.cursor()
    df = pd.read_sql_query(query, connection)
    connection.close()

    return df


if __name__ == "__main__":
    pass
