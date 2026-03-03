import instaloader
import time
from itertools import islice
from datetime import datetime
import random # for a more human scroll time (immitation not robotic 5s each time)

import sys

# from dev made files 
# from gemini_summariser import get_event_summary 

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

# 2. Get target username from command line argument (optional)
if len(sys.argv) > 1:
    target_username = sys.argv[1]
else:
    target_username = 'umsuactivities'

print(f"--- Attempting to scrape {target_username} anonymously ---")

try:
    # 3. Load the Profile
    profile = instaloader.Profile.from_username(L.context, target_username)
    
    # 4. Iterate over posts
    # usage of islice() allows us to only grab the newest 3 posts to avoid hitting rate limits
    
    posts = islice(profile.get_posts(), MAX_POSTS_PER_SESSION)
    last_checked_date = datetime.fromisoformat('2026-01-29')
    
    for post in posts:
        date_t = post.date
        if (post.is_pinned and date_t <= last_checked_date): continue;
        if (date_t <= last_checked_date): break

        print("\n" + "="*30)
        print(f"Date: {post.date_local}")
        print(f"time metadata utc: {post.date}")

        print(f"Likes: {post.likes}")
        
        # 5. The Payload: The Caption
        # This is where we will eventually look for keywords like "Pizza" or "BBQ"
        # summarised_cap = get_event_summary(post.caption)
        #print(f"Caption: {summarised_cap}") 
        print(f"Caption: {post.caption}") # @SUMMARISER TO REMOVE

        print(f"Link: https://www.instagram.com/p/{post.shortcode}/")



        print("="*30)




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
