import subprocess 
import os
from dotenv import load_dotenv

load_dotenv()

# all preset in env file
username = os.getenv("username")


# load dummy account cookies from your browser (can change if not chrome)
subprocess.run("instaloader --load-cookies chrome")

# copy directories over - designed for linux/macos filesytem (can setup using pathlib for total support)
subprocess.run(f"cp -r ~/.config/instaloader/session-{username} /opt/insta_news_data/config/instaloader/session-{username}")

