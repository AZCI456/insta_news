import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://umsu.unimelb.edu.au/"

import os
import sqlite3
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

DB_PATH = os.getenv("insta_news_db_path")

def extract_club_data(url: str) -> dict | None:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Target the specific classes you found
    # It's so easy.......... ☺️ thanks umsu website devs 😁
    insta_tag = soup.find('a', class_='msl_instagram')
    email_tag = soup.find('a', class_='msl_email')

    # TODO: grey out in the websites dropdown if no instagram is found
    # # Logic: Skip if email is missing (as per your requirement)
    # if not insta_tag:
    #     return None

    email = email_tag.get_text(strip=True) if email_tag else None
    
    # Extract username from the href: //instagram.com/unimelb.bts -> unimelb.bts
    insta_url = insta_tag['href'] if insta_tag else None
    username = insta_url.rstrip('/').split('/')[-1] if insta_url else None

    return {
        "name": soup.find('h1').get_text(strip=True),
        "email": email,
        "username": username,
        "insta_url": insta_url,
        "umsu_url": url
    }

def collect_all_club_links(base_url: str = BASE_URL) -> list[str]:
    """Extract full detail-page URLs from the clubs listing. Uses ul.msl_organisation_list > li > a.msl-gl-link."""
    resp = requests.get(urljoin(base_url, "/buddy-up/clubs/clubs-listing/"), timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    links = []
    # select the unordered list of clubs (this is the tag in their html)
    # note that the list item has a data-msl-grouping-id attribute which is the club's id
    for li in tqdm(soup.select("ul.msl_organisation_list li[data-msl-grouping-id]"), desc="Extracting club links"):
        # select the anchor tag within the list item
        a = li.select_one("a.msl-gl-link")
        if a and a.get("href"):
            # append the full URL to the list
            links.append(urljoin(base_url, a["href"]))
    return links

    # TODO: inside that unordered list each club has keywords attached to it (IT, Industry, etc.)
    # we need to extract these keywords and relate to the club using a junction table / associative entity
    # just populate all the keywords with a surrogate key and then link as a foreign primary key  in the junction table with the club's id
    # this will allow us to easily query for clubs by keyword and vice versa
    # eg (club_id, keyword_id) -> Club and Keyword entity table


def insert_club_data(club_data: dict) -> None:
    # get the file from the current directory and read it into memory
    sql_path = os.path.join(os.path.dirname(__file__), "upsert_club.sql")
    with open(sql_path, "r") as f:
        upsert_sql = f.read()

    # add to db updated values or insert new if not exists (SOOOO MUCH EASIER THAN DUCK DB!!!!!!)
    with sqlite3.connect(DB_PATH) as con:
        cursor = con.cursor()
        cursor.execute(
            upsert_sql,
            {
                "name": club_data["name"],
                "email": club_data["email"],
                "username": club_data["username"],
                "insta_url": club_data["insta_url"],
                "umsu_url": club_data["umsu_url"],
            },
        )
        con.commit()

def main():
    club_links = collect_all_club_links()
    #print(club_links)
    for link in tqdm(club_links, desc="Extracting and Loading club data to DB...", total=len(club_links)):
        club_data = extract_club_data(link)
        if club_data:
            insert_club_data(club_data)

if __name__ == "__main__":
    main()