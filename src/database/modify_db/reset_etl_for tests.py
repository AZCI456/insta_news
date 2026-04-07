from pathlib import Path
import sqlite3
from dotenv import load_dotenv
import os
load_dotenv()
DB_PATH = os.getenv("insta_news_db_path")

if __name__ == "__main__":
    conn = sqlite3.Connection(DB_PATH)
    cursor = conn.cursor()


    print("Are you sure you wish to proceed [y/n]: ", end='')
    response = input()
    if (response != 'y'):
        conn.close()
        exit(0)

    # truncate not supported by sqllite
    cursor.execute("DELETE FROM posts;")
    
    cursor.execute("UPDATE clubs set last_scraped_at = datetime('now', '-7 days') where last_scraped_at is not null;")
    
    conn.commit()
    conn.close()
