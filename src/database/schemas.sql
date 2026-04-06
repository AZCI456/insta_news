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
    last_scraped_at DATETIME DEFAULT NULL -- set when a user subscribes (manage page). NULL means "not approved for scraping yet"
    -- isactive implicit from associative entity
);

-- 2. Posts table
-- No ON DELETE CASCADE so reimports/updates won't cascade deletions.
CREATE TABLE IF NOT EXISTS posts (
    post_id INTEGER PRIMARY KEY,  -- surrogate - fast insert / indexing - current auto assginement - needs to be explicit when moving to postgre
    club_id TEXT, -- from the loop of subscribed to clubs (join table with users)
    caption TEXT,
    likes INTEGER,
    time_metadata_utc DATETIME,
    date_scraped DATETIME,
    shortcode TEXT UNIQUE, -- globally unique identifier on instagram
    -- GEM fields (uncomment when ready to use)
    -- food_summary JSON,
    -- process_status TEXT DEFAULT 'pending',
    FOREIGN KEY (club_id) REFERENCES clubs(club_id)
);

-- 3. Food events table (dependent on posts)
-- Note make events table for gemini memory of all clubs and then have a field active or not based on whether 
-- the time of the event is in the past or future
CREATE TABLE IF NOT EXISTS food_events (
    post_id TEXT PRIMARY KEY,  -- what to do if multiple posts link to the same food event?
    has_food BOOLEAN NOT NULL,
    food_type TEXT,
    event_date DATE,
    start_time TIME,
    end_time TIME,
    location TEXT,
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

CREATE TABLE IF NOT EXISTS ai_summaries (
    summary_id INTEGER PRIMARY KEY,
    club_id INTEGER NOT NULL,
    header TEXT, -- this is the title of the Excerpt
    content TEXT,
    FOREIGN KEY (club_id) REFERENCES club(club_id)
);

-- Junction table for all the used posts in the summary
CREATE TABLE IF NOT EXISTS summary_to_posts (
    summary_id INTEGER,
    post_id INTEGER, 
    PRIMARY KEY (summary_id, post_id),
    FOREIGN KEY (summary_id) REFERENCES ai_summaries(summary_id),
    FOREGIN KEY (post_id) REFERENCES posts(post_id)
) 

-- 6. Keywords Table (all the different identifier keywords for the club)
-- Master list of all possible keywords (unique/normalized):
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id INTEGER PRIMARY KEY,
    keyword TEXT UNIQUE NOT NULL  -- no duplicate keywords
);

-- Junction table to connect clubs and keywords in a many-to-many relationship:
-- if you see the raw json this represents the links
CREATE TABLE IF NOT EXISTS club_keywords (
    club_id INTEGER,
    keyword_id INTEGER,
    PRIMARY KEY (club_id, keyword_id), -- relation between the two tables
    FOREIGN KEY (club_id) REFERENCES clubs(club_id),
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id)
);

-- Teaching comment:
-- This normalization pattern makes it easy to:
--   - Find all keywords for a club: JOIN club_keywords ON club_id and then keywords ON keyword_id.
--   - Find all clubs with a given keyword.
--   - Avoid duplicate/typo'd keywords across the clubs.