# UMSU / MSL clubs listing scraper

Beautiful Soup boilerplate for the buddy-up clubs listing.

- **`listing_scraper.py`** – fetches the main listing page, parses each `li[data-msl-grouping-id]`, extracts `data-msl-keywords`, join path, and club name. Optionally writes to DB via `DB_tools.club_keywords`.
- **Child script (you)** – hit each club’s `join_path` URL to scrape email/Instagram and then call `store_club_with_keywords(conn, club_id, name=..., email=...)`.

Run from repo root so `DB_tools` is importable:

```bash
cd /path/to/insta_news
PYTHONPATH=. python etl/UMSU_DATA_SCRAPING/listing_scraper.py
```

Dependencies: `requests`, `beautifulsoup4` (e.g. `pip install requests beautifulsoup4`).
