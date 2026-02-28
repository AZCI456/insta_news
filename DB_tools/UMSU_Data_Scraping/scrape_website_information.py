import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://msl.unimelb.edu.au"


def extract_club_data(url: str) -> dict | None:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Target the specific classes you found
    insta_tag = soup.find('a', class_='msl_instagram')
    email_tag = soup.find('a', class_='msl_email')

    # Logic: Skip if email is missing (as per your requirement)
    if not email_tag:
        return None

    email = email_tag.get_text(strip=True)
    
    # Extract username from the href: //instagram.com/unimelb.bts -> unimelb.bts
    insta_url = insta_tag['href'] if insta_tag else None
    username = insta_url.rstrip('/').split('/')[-1] if insta_url else None

    return {
        "name": soup.find('h1').get_text(strip=True),
        "email": email,
        "username": username
    }

def collect_all_club_links(base_url: str = BASE_URL) -> list[str]:
    """Extract full detail-page URLs from the clubs listing. Uses ul.msl_organisation_list > li > a.msl-gl-link."""
    resp = requests.get(urljoin(base_url, "/buddy-up/clubs/clubs-listing/"), timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    links = []
    for li in soup.select("ul.msl_organisation_list li[data-msl-grouping-id]"):
        a = li.select_one("a.msl-gl-link")
        if a and a.get("href"):
            links.append(urljoin(base_url, a["href"]))
    return links