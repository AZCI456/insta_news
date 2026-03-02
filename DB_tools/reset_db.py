import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("insta_news_db_path")

def load_schema(connection: sqlite3.Connection) -> None:
    """
    Load and execute the schema.sql file in this directory into the given connection.
    """
    this_dir = Path(__file__).resolve().parent
    schema_path = this_dir / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"schema.sql not found at {schema_path}")

    with schema_path.open("r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Ensure foreign key constraints are enforced.
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.executescript(schema_sql)
    connection.commit()


def reset_database(db_path: str) -> None:
    """
    Delete the existing database file (if it exists) and recreate it from schema.sql.
    """
    if not db_path:
        raise ValueError("DB_PATH is empty. Please set DB_PATH in reset_db.py.")

    # Remove existing database file to fully replace the old database.
    if os.path.exists(db_path):
        os.remove(db_path)
    else:
        print(f"Database file not found at {db_path}")
        print(f"Creating new database file at {db_path}")

    # Ensure parent directory exists.
    parent_dir = os.path.dirname(db_path)
    if parent_dir and not os.path.exists(parent_dir):
        print(f"Parent directory not found at {parent_dir}")
        print(f"Creating parent directory at {parent_dir}")
        os.makedirs(parent_dir, exist_ok=True)

    # Create new database and apply schema.
    with sqlite3.connect(db_path) as conn:
        load_schema(conn)

    print(f"Database reset and schema applied at: {db_path}")


if __name__ == "__main__":
    reset_database(DB_PATH)

