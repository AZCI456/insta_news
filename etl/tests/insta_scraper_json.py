import instaloader
import time
from itertools import islice
from datetime import datetime
import random # for a more human scroll time (immitation not robotic 5s each time)
# for the insta username (not to expose and get flagged on public repo lol)
import os 
from dotenv import load_dotenv

# for serialisation
import json

# from dev made files 
from gemini_summariser import get_event_summary 

MAX_POSTS_PER_SESSION = 10

# 1. Initialize Instaloader WITHOUT login (Anonymous mode)
# We disable downloading pictures/videos to save bandwidth and speed up the test.
L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False, 
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False
)

# With login
# Load environment variables from .env file
load_dotenv()

username = os.getenv("insta_username") # replace with your username 
session_path = os.path.expanduser(f"~/.config/instaloader/session-{username}")

try:
    with open(session_path, 'rb') as f:
        L.load_session_from_file(username, f)
    print("Authentication successful via session file.")
except FileNotFoundError:
    print(f"Error: Session file not found at {session_path}")

# 2. Define your target (Public Account)
# Try: 'cissa_unimelb', 'unimelb_misc', 'unimelbcpc', 'umsuactivities'
target_username = 'umsuactivities' 

print(f"--- Attempting to scrape {target_username} anonymously ---")

try:
    # 3. Load the Profile
    profile = instaloader.Profile.from_username(L.context, target_username)
    
    # 4. Iterate over posts
    # usage of islice() allows us to only grab the newest 3 posts to avoid hitting rate limits
    
    posts = islice(profile.get_posts(), MAX_POSTS_PER_SESSION)
    last_checked_date = datetime.fromisoformat('2026-01-29')
    
    with open('output.jsonl', 'a') as f:
        f.write('\n\n\n')  # break between tests 

    for post in posts:
        date_t = post.date
        if (post.is_pinned and date_t <= last_checked_date): continue;
        if (date_t <= last_checked_date): break


        data = {
            "date_local": post.date_local.isoformat(),
            "time_metadata_utc": post.date.isoformat(),
            "likes": post.likes,
            # "caption": get_event_summary(post.caption),
            "caption": "NO SUMMARY YET @ SUMMARISER",  # NOTE: REMOVE
            "link": f"https://www.instagram.com/p/{post.shortcode}/",
        }

        with open('output.jsonl', 'a') as f:
            json.dump(data, f)
            f.write('\n')  # newline formatting 

        print(f"Processed Post on {post.date_local}")

        # 6. CRITICAL: The "Human" Pause
        # Even for a test, sleep to avoid an immediate 429 Error/Soft Ban on your IP
        time.sleep(random.randint(4, 8)) 


except instaloader.ConnectionException as e:
    print(f"\n[!] Connection Error: {e}")
    print("Instagram likely detected the script. This is where Proxies would kick in.")
except instaloader.LoginRequiredException:
    print(f"\n[!] Login Required: Instagram is blocking anonymous access for this specific IP/Account.")
except Exception as e:
    print(f"\n[!] Error: {e}")
