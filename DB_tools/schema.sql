-- Schema for insta_news SQLite database

-- 1. Clubs table (account metadata)
CREATE TABLE IF NOT EXISTS clubs (
    name TEXT,
    email TEXT, -- free on the scraper they all have emails
    -- can do website as well but not useful info for me as v static most of the time + 90% don't have
    username VARCHAR PRIMARY KEY,
    insta_url TEXT,
    umsu_url TEXT,
    last_scraped_at DATETIME DEFAULT NULL
    -- isactive implicit from associative entity
);

-- inspect the webpage total data goldmine for indexing (all the heavy lifting done)
-- 2. Keywords (unique tags from data-msl-keywords; many-to-many with clubs)
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE
);

-- 3. Club–keyword junction (links clubs to keywords for discovery search)
CREATE TABLE IF NOT EXISTS club_keywords (
    club_username VARCHAR,
    keyword_id INTEGER,
    PRIMARY KEY (club_username, keyword_id),
    FOREIGN KEY (club_username) REFERENCES clubs(username),
    FOREIGN KEY (keyword_id) REFERENCES keywords(id)
);

-- 4. Posts table (no ON DELETE CASCADE so reimports/updates won't cascade)
CREATE TABLE IF NOT EXISTS posts (
    post_id TEXT PRIMARY KEY,
    username TEXT,
    caption TEXT,
    timestamp DATETIME,
    -- GEM fields (uncomment when ready to use)
    -- food_summary JSON,
    -- process_status TEXT DEFAULT 'pending',
    FOREIGN KEY (username) REFERENCES clubs(username)
);

-- 5. Food events table (dependent on posts)
CREATE TABLE IF NOT EXISTS food_events (
    post_id TEXT PRIMARY KEY,              -- or (post_id, event_idx) if multi
    has_food BOOLEAN NOT NULL,
    event_date DATE,
    start_time TIME,
    end_time TIME,
    location TEXT,
    description TEXT,
    confidence REAL,
    FOREIGN KEY (post_id) REFERENCES posts(post_id)
);

-- 6. Users (identity, privacy-focused)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_hash TEXT UNIQUE NOT NULL,      -- SHA256 hex
    encrypted_email TEXT NOT NULL,        -- AES-encrypted, decryptable
    manage_token TEXT UNIQUE NOT NULL,    -- UUID v4 ("magic link" token)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. Subscriptions (join table: users ↔ clubs)
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER,
    club_id TEXT,
    PRIMARY KEY (user_id, club_id),
    FOREIGN KEY (club_id) REFERENCES clubs(username),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    -- NOTE: no ON DELETE CASCADE on purpose
);

