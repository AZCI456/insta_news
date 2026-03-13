-- Schema for insta_news SQLite database

-- 1. Clubs table (account metadata)
-- TODO: surrogate key some clubs don't have a username 
CREATE TABLE IF NOT EXISTS clubs (
    club_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    username VARCHAR UNIQUE, -- can be null for some clubs (in the db so we can tell the user your club doesn't have insta)
    insta_url TEXT,
    umsu_url TEXT,
    umsu_grouping_id int,
    last_scraped_at DATETIME DEFAULT NULL -- beats last scraped post id as post's can be deleted (loops through EVERYTHING)
    -- isactive implicit from associative entity
);

-- 2. Posts table
-- No ON DELETE CASCADE so reimports/updates won't cascade deletions.
CREATE TABLE IF NOT EXISTS posts (
    post_id TEXT PRIMARY KEY,  -- globally unique on insta
    club_id TEXT, -- from the loop of subscribed to clubs (join table with users)
    caption TEXT,
    timestamp DATETIME,
    -- GEM fields (uncomment when ready to use)
    -- food_summary JSON,
    -- process_status TEXT DEFAULT 'pending',
    FOREIGN KEY (club_id) REFERENCES clubs(club_id)
);

-- 3. Food events table (dependent on posts)
-- TODO: add slide_id to the primary key (so we can have slides of captions per post - unlikely but possible)
-- NOTE: MAYBE NOT ACTUALLY - just loop through and concatenate the captions into one big string - then feed to gemini
CREATE TABLE IF NOT EXISTS food_events (
    post_id TEXT PRIMARY KEY,  -- what to do if multiple posts link to the same food event?
    has_food BOOLEAN NOT NULL,
    event_date DATE,
    start_time TIME,
    end_time TIME,
    location TEXT,
    description TEXT,
    confidence REAL,
    FOREIGN KEY (post_id) REFERENCES posts(post_id)
);

-- 4. Users (identity, privacy-focused)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_hash TEXT UNIQUE NOT NULL,      -- SHA256 hex
    encrypted_email TEXT NOT NULL,        -- AES-encrypted, decryptable
    manage_token TEXT UNIQUE NOT NULL,    -- UUID v4 ("magic link" token)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN DEFAULT FALSE -- via magic link verification email
);

-- 5. Subscriptions (join table: users ↔ clubs)
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER,
    club_id INTEGER,
    PRIMARY KEY (user_id, club_id),
    FOREIGN KEY (club_id) REFERENCES clubs(club_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
    -- NOTE: no ON DELETE CASCADE on purpose
);

-- 6. Keywords Table (all the different identifier keywords for the club)
-- Keywords should be a stand-alone entity (table) because:
-- 1. Many clubs can share the same keyword (e.g., "Technology", "Sports", etc.),
--    and each club can have multiple keywords (many-to-many relationship).
-- 2. With a dedicated 'keyword_id' as a surrogate (autoincrement integer) key,
--    we normalize the keywords, help with storage efficiency, and make keyword lookups/joining across clubs much easier.
--    Otherwise we'd be writing/duplicating strings over and over and struggle with changes, typos, and efficient searching.
--
-- 3. To represent club-keyword relationships, we use a linking/junction table
--    (club_keywords in this case), which ties club_id <-> keyword_id (both foreign keys).

-- Master list of all possible keywords (unique/normalized):
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT UNIQUE NOT NULL  -- no duplicate keywords
);

-- Junction table to connect clubs and keywords in a many-to-many relationship:
CREATE TABLE IF NOT EXISTS club_keywords (
    club_id INTEGER,
    keyword_id INTEGER,
    PRIMARY KEY (club_id, keyword_id), -- each pair is unique
    FOREIGN KEY (club_id) REFERENCES clubs(club_id),
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id)
);

-- Teaching comment:
-- This normalization pattern makes it easy to:
--   - Find all keywords for a club: JOIN club_keywords ON club_id and then keywords ON keyword_id.
--   - Find all clubs with a given keyword.
--   - Avoid duplicate/typo'd keywords across the clubs.