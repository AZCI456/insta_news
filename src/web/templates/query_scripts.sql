-- I use DBeaver to look at the db and examine stuff below are a few
-- of the queries I usually run

-- see the schema (can do in side menu as well)
PRAGMA table_info(clubs);


-- find the most popular keywords
select k.keyword, count(*) 
from club_keywords ck 
left join keywords k on k.keyword_id  = ck.keyword_id  
group by k.keyword 
order by count(*) desc;

