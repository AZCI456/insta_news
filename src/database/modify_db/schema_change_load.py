from pathlib import Path
import sqlite3
from dotenv import load_dotenv
import os
load_dotenv()
DB_PATH = os.getenv("insta_news_db_path")

def load_schema(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    sql_directory = Path(__file__).resolve().parent.parent
    schema_path = sql_directory / "schemas.sql"
    with schema_path.open("r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)


def remove_empty_tables(conn: sqlite3.Connection) -> None:
    '''
    Allows us to upsert new column names or
    get rid of unused tables before importing the fresh 
    schema
    '''
    cursor = conn.cursor()

    table_lst = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    for (table_name,) in table_lst.fetchall():
        # Check if the table has any rows
        res = cursor.execute(f"SELECT count(*) FROM {table_name};")
        count = res.fetchone()[0]
        if count:
            continue  # Only drop empty tables

        # Delete empty table - will be reinserted if necessary in the next function call
        conn.execute(f"DROP TABLE {table_name};")
        conn.commit()

    

if __name__ == "__main__":
    conn = sqlite3.Connection(DB_PATH)

    remove_empty_tables(conn)

    load_schema(conn)
