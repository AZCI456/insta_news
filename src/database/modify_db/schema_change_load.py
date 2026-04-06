from pathlib import Path
import sqlite3
from dotenv import load_dotenv
import os
load_dotenv()
DB_PATH = os.getenv("insta_news_db_path")

def load_schema(conn: sqlite3.Connection) -> None:
    sql_directory = Path(__file__).resolve().parent.parent
    schema_path = sql_directory / "schemas.sql"
    with schema_path.open("r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)

if __name__ == "__main__":
    conn = sqlite3.Connection(DB_PATH)

    load_schema(conn)