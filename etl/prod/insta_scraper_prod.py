import instaloader
import time
from itertools import islice
from datetime import datetime, timezone  
import random
import os
from dotenv import load_dotenv
import json

#from python files
import sqlite3
import data_paths  # local module in this folder: creates/returns standard data directories + file paths
from gemini_summariser import gemini_summariser  # production Gemini summariser (writes derived summary JSON)

load_dotenv()

DB_PATH = os.getenv("insta_news_db_path")



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
    club_id: int,
    target_username: str,
    last_checked_date: datetime,
   # output_path: str, # TODO: make this a variable in the env file
    batch_list: list,
    con: sqlite3.Connection  # all passed in through reference so stays alive
):
    print(f"--- Attempting to scrape {target_username} ---")

    profile = instaloader.Profile.from_username(loader.context, target_username)
    posts =  profile.get_posts() # islice(profile.get_posts(), max_posts)

    # teaching comment: this helper reads `insta_news_data_root` from `.env` and gives us
    # consistent folders for raw JSONL + derived summaries (creating missing dirs safely).
    paths = data_paths.get_paths()

    # keeps each run grouped together on disk.
    run_date_yyyy_mm_dd = datetime.now().date().isoformat()

    # currently only one caption per multislide post so this works perfectly
    # NOTE: pinned posts no longer supported by the API - broken by insta upsterasm changes
    for i,post in enumerate(posts):

        date_t = post.date_utc.replace(tzinfo=timezone.utc)
        # see if this is a stale pinned post
        # insta allows only 3 pinned posts per profile
        # assume first 3 pinned - wont actually ingest if old anyway
        if date_t <= last_checked_date:
            if i < 4:
                continue
            else:
                break

        # caption_summary = get_event_summary(post.caption)
        caption = post.caption

        # raw JSONL path for this club and this run date
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
            "date_scraped": datetime.now().isoformat() # so gemini has context if the event has passed or not
        }

        # db insert
        con.execute("INSERT INTO posts (club_id, caption, likes," \
                    " time_metadata_utc, date_scraped, shortcode)"
                    "VALUES (?,?,?,?,?,?)",
                    (club_id, caption, post.likes, post.date.isoformat(),
                      datetime.now().isoformat(), post.shortcode))

        # jsonl for gemini as well as on droplet storage
        with open(raw_jsonl_path, "a") as f:
            json.dump(data, f)
            f.write("\n")

        batch_list.append(data)

        print(f"Processed Post on {post.date_local}")
        time.sleep(random.randint(4, 8))

    # update the last_scraped_at date
    con.execute("UPDATE clubs SET last_scraped_at = ? WHERE username = ?", (datetime.now().isoformat(), target_username))
    con.commit()


def main():
    username, session_path = load_config()
    loader = create_loader()
    load_session(loader, username, session_path)

    con = sqlite3.connect(DB_PATH)

    # get all the clubs that have been approved for scraping 
    targets = con.execute(
        "SELECT club_id, username, last_scraped_at FROM clubs WHERE last_scraped_at IS NOT NULL"
    ).fetchall()

    #print(f"Targets: {targets}");
    #exit()
    
    batch_process_list = []
    BATCH_PROCESS_THREASHHOLD = 50

    try:
        for target in targets:
            if len(batch_process_list) >= BATCH_PROCESS_THREASHHOLD:
                gemini_summariser(batch_process_list, batch_size=BATCH_PROCESS_THREASHHOLD)
                batch_process_list.clear()  # teaching comment: prevent resending the same items in the next batch

            club_id = target[0]
            target_username = target[1]
            if (not target_username): continue

            # load last_scraped_at as a timezone aware datetime so we can compare to post.date_utc with tzinfo stripped
            last_checked_date = datetime.fromisoformat(target[2]).replace(tzinfo=timezone.utc)
            scrape_profile(
                loader=loader,
                club_id=club_id,
                target_username=target_username,
                last_checked_date=last_checked_date,
                batch_list = batch_process_list,
                con=con
            )
        
        if len(batch_process_list):
            gemini_summariser(batch_process_list, batch_size=BATCH_PROCESS_THREASHHOLD)
            batch_process_list.clear()

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
