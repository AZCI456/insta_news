import instaloader
import time
from itertools import islice
from datetime import datetime
import random
import os
from dotenv import load_dotenv
import json

#from python files
import sqlite3


MAX_POSTS_PER_SESSION = 10


def load_config():
    load_dotenv()
    username = os.getenv("insta_username")
    if not username:
        raise RuntimeError("Environment variable 'insta_username' is not set.")

    session_path = os.path.expanduser(
        f"/opt/insta_news_data/config/instaloader/session-{username}"
    )
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
    target_username: str,
    max_posts: int,
    last_checked_date: datetime,
    output_path: str
   # con: sqlite3.Connection  # all passed in through reference so stays alive
):
    print(f"--- Attempting to scrape {target_username} ---")

    profile = instaloader.Profile.from_username(loader.context, target_username)
    posts = islice(profile.get_posts(), max_posts)

    with open(output_path, "a") as f:
        f.write("\n\n\n")
        f.write(f"{datetime.now()}: beginning RUN")

    for post in posts:
        date_t = post.date
        if post.is_pinned and date_t <= last_checked_date:
            continue
        if date_t <= last_checked_date:
            break

        # caption_summary = get_event_summary(post.caption)
        caption_summary = "NO SUMMARY YET @ SUMMARISER"

        data = {
            "date_local": post.date_local.isoformat(),
            "time_metadata_utc": post.date.isoformat(),
            "likes": post.likes,
            "caption": caption_summary,
            "link": f"https://www.instagram.com/p/{post.shortcode}/",
        }

        with open(output_path, "a") as f:
            json.dump(data, f)
            f.write("\n")

        print(f"Processed Post on {post.date_local}")
        time.sleep(random.randint(4, 8))


def main():
    username, session_path = load_config()
    loader = create_loader()
    load_session(loader, username, session_path)

    target_username = "umsuactivities"
    last_checked_date = datetime.fromisoformat("2026-01-29")
    output_path = "output.jsonl"

    # con = sqlite3.connect("/opt/insta_news_data/")

    try:
        scrape_profile(
            loader=loader,
            target_username=target_username,
            max_posts=MAX_POSTS_PER_SESSION,
            last_checked_date=last_checked_date,
            output_path=output_path
        )
    except instaloader.ConnectionException as e:
        print(f"\n[!] Connection Error: {e}")
        print("Instagram likely detected the script. This is where Proxies would kick in.")
    except instaloader.LoginRequiredException:
        print(
            "\n[!] Login Required: Instagram is blocking anonymous access for this specific IP/Account."
        )
    except Exception as e:
        print(f"\n[!] Error: {e}")


if __name__ == "__main__":
    main()
