"""Query the db
"""

import sqlite3 as sql

import pandas as pd

path_to_db = "monitor.db"


def load(query, *args, path=path_to_db) -> pd.DataFrame:
    """Converts sqlite3 db query to pandas df

    @param[in] query - str with direct sql query (for more complex queries)
    @param[in] args - query args (passed into query string)
    @param[in] path - path to database
    @return df - pandas data frame with specified table and conditions
    """
    connection = sql.connect(path)
    c = connection.cursor()

    if args:
        # Sanitized query
        df = pd.read_sql_query(query, connection, params=args)
    else:
        df = pd.read_sql_query(query, connection)

    connection.close()

    return df


if __name__ == "__main__":
    pass
