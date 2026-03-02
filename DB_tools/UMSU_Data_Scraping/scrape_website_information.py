import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://umsu.unimelb.edu.au/"


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
    for li in soup.select("ul.msl_organisation_list li[data-msl-grouping-id]"):
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


def main():
    club_links = collect_all_club_links()
    #print(club_links)
    for link in club_links:
        club_data = extract_club_data(link)
        print(club_data)
        break

if __name__ == "__main__":
    main()