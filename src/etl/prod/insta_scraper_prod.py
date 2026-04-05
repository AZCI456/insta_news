import instaloader
import time
from datetime import datetime, timezone
import random
import os
from dotenv import load_dotenv
import json
import sqlite3

from src.etl.prod import data_paths
from src.etl.prod.gemini_summariser import gemini_summariser

load_dotenv()
DB_PATH = os.getenv("insta_news_db_path")


def load_config():
    load_dotenv()
    username = os.getenv("insta_username")
    if not username:
        raise RuntimeError("Environment variable 'insta_username' is not set.")
    session_path = os.path.expanduser(f"/opt/insta_news_data/config/instaloader/session-{username}")
    return username, session_path


def create_loader():
    return instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
    )


def load_session(loader: instaloader.Instaloader, username: str, session_path: str):
    try:
        loader.load_session_from_file(username, session_path)
        print("Authentication successful via session file.")
    except FileNotFoundError:
        print(f"Error: Session file not found at {session_path}")


def scrape_profile(
    loader: instaloader.Instaloader,
    club_id: int,
    target_username: str,
    last_checked_date: datetime,
    batch_list: list,
    con: sqlite3.Connection,
):
    print(f"--- Attempting to scrape {target_username} ---")
    profile = instaloader.Profile.from_username(loader.context, target_username)
    posts = profile.get_posts()
    paths = data_paths.get_paths()
    run_date_yyyy_mm_dd = datetime.now().date().isoformat()

    for i, post in enumerate(posts):
        date_t = post.date_utc.replace(tzinfo=timezone.utc)
        if date_t <= last_checked_date:
            if i < 4:
                continue
            break

        caption = post.caption
        raw_jsonl_path = paths.raw_posts_jsonl_path(club_id=club_id, date_yyyy_mm_dd=run_date_yyyy_mm_dd)
        data_paths.ensure_dir(raw_jsonl_path.parent)

        data = {
            "club_id": club_id,
            "username": target_username,
            "post_id": post.shortcode,
            "date_local": post.date_local.isoformat(),
            "time_metadata_utc": post.date.isoformat(),
            "likes": post.likes,
            "caption": caption,
            "link": f"https://www.instagram.com/p/{post.shortcode}/",
            "date_scraped": datetime.now().isoformat(),
        }

        con.execute(
            "INSERT INTO posts (club_id, caption, likes, time_metadata_utc, date_scraped, shortcode) VALUES (?,?,?,?,?,?)",
            (club_id, caption, post.likes, post.date.isoformat(), datetime.now().isoformat(), post.shortcode),
        )

        with open(raw_jsonl_path, "a", encoding="utf-8") as f:
            json.dump(data, f)
            f.write("\n")

        batch_list.append(data)
        print(f"Processed Post on {post.date_local}")
        time.sleep(random.randint(4, 8))

    con.execute("UPDATE clubs SET last_scraped_at = ? WHERE username = ?", (datetime.now().isoformat(), target_username))
    con.commit()


def main():
    username, session_path = load_config()
    loader = create_loader()
    load_session(loader, username, session_path)
    con = sqlite3.connect(DB_PATH)
    targets = con.execute("SELECT club_id, username, last_scraped_at FROM clubs WHERE last_scraped_at IS NOT NULL").fetchall()

    batch_process_list = []
    batch_process_threshold = 50

    try:
        for target in targets:
            if len(batch_process_list) >= batch_process_threshold:
                gemini_summariser(batch_process_list, batch_size=batch_process_threshold)
                batch_process_list.clear()

            club_id = target[0]
            target_username = target[1]
            if not target_username:
                continue

            last_checked_date = datetime.fromisoformat(target[2]).replace(tzinfo=timezone.utc)
            scrape_profile(
                loader=loader,
                club_id=club_id,
                target_username=target_username,
                last_checked_date=last_checked_date,
                batch_list=batch_process_list,
                con=con,
            )

        if len(batch_process_list):
            gemini_summariser(batch_process_list, batch_size=batch_process_threshold)
            batch_process_list.clear()

    except instaloader.ConnectionException as e:
        print(f"\n[!] Connection Error: {e}")
        print("Instagram likely detected the script. This is where Proxies would kick in.")
    except instaloader.LoginRequiredException:
        print("\n[!] Login Required: Instagram is blocking anonymous access for this specific IP/Account.")
    except Exception as e:
        print(f"\n[!] Error: {e}")


if __name__ == "__main__":
    main()

