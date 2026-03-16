-- remove Dead clubs with no subscribers (set into hibernation?)
UPDATE clubs
SET last_scraped_at = NULL -- or hibernate on
WHERE last_scraped_at IS NOT NULL 
    AND club_id NOT IN (
        SELECT DISTINCT club_id FROM subscriptions
    );