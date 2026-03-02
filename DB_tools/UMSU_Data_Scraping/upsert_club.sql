INSERT INTO clubs (name, email, username, insta_url, umsu_url)
VALUES (:name, :email, :username, :insta_url, :umsu_url)
ON CONFLICT(username) DO UPDATE SET
    name      = excluded.name,
    email     = excluded.email,
    insta_url = excluded.insta_url,
    umsu_url  = excluded.umsu_url;
