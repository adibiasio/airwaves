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


def load(table, direct_query=None, cols=None, conditions=[], condition_op="AND", datetimes=[], distinct=False, path=path_to_db) -> pd.DataFrame:
    """Converts sqlite3 db to pandas df

    @param[in] table - name of table to load
    @param[in] cols - List of column(s) to load, if specified, only values from those column(s) will be selected 
    @param[in] conditions - list of (col, value(s), NOT_boolean) pairs used to filter the table
                            NOT_boolean: Bool specifying whether the sqlite3 NOT function should be 
                            applied to the condition, default is false if not specified
    @param[in] direct_query - str with direct sql query (for more complex queries)
    @param[in] condition_op - SQL operator used between WHERE clauses
    @param[in] datetimes -  List of names of unix timestamp columns, indicates data should be selected as datetimes
                            This column should still be included under the "cols" kwarg
    @param[in] distinct - Boolean, indicates whether to apply DISTINCT 
    @param[in] path - path to database
    @return df - pandas data frame with specified table and conditions
    """
    connection = sql.connect(path)
    c = connection.cursor()

    if not direct_query:
        for i, condition in enumerate(conditions):
            if len(condition) == 2:
                conditions[i] += (False,)

        where = ""

        # Building WHERE clause
        for i, condition in enumerate(conditions):
            where += " WHERE" if i == 0 else ""
            where += " NOT" if condition[2] else ""

            if type(condition[1]) == list and len(condition[1]) > 1:
                where += " ("
                for index, value in enumerate(condition[1]):
                    where += f"{condition[0]} = {condition[1][index]}"
                    where += " OR " if index + 1 < len(condition[1]) else ""
                where += ")"
            else:
                where += f" {condition[0]} = {condition[1]}"
            where += " " + condition_op if len(conditions) > 1 and i + 1 < len(conditions) else ""

        # Building SELECT region
        if cols and [exists_in_db(col, table) for col in cols]:
            select_region = ""
            for i, col in enumerate(cols):
                select_region += col + ", " if i + 1 < len(cols) else col
        else:
            select_region = "*"

        # Checking for DISTINCT
        if distinct:
            select_region = "DISTINCT " + select_region

        query = f"SELECT {select_region} FROM {table}{where}"
    else:
        query = direct_query

    df = pd.read_sql_query(query, connection)
    connection.close()

    # Converting UNIX timestamp to local datetime
    for datetime in datetimes:
        if datetime in df.columns:
            # shift time.timezone by 1 hour to match GMT offset
            df[datetime] = pd.to_datetime(df[datetime], unit="s") -  pd.DateOffset(seconds=time.timezone-3600)

    return df


if __name__ == "__main__":
    pass
