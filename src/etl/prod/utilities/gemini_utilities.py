
import typing
from typing import Any, Dict, List
from collections import defaultdict

import sqlite3


def group_by_club(all_posts: Dict[int, List[Dict[str, Any]]]) -> dict:
    
    # typing to reillustrate format - dict str-any is the posts struct that 
    # we made in the prev function
    club_posts: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for post in all_posts:
        club_id = post.get("club_id")
        if club_id is None:
            # If club_id is missing, we can't route it to the right folder.
            # Skip rather than corrupting output.
            continue
        club_posts[int(club_id)].append(post)

    return club_posts

def create_club_lookup_table(conn: sqlite3.Connection) -> Dict[int, str]:
    '''
    creates full table (approx 250 entries) for all of the clubs so that name
    insertion is an easier O(1) lookup when passing into the ai model
    '''
    
    cursor = conn.cursor()

    id_to_name: Dict[int, str] = dict()
    club_information = cursor.execute("SELECT club_id, name FROM clubs")
    # assert(club_infromation) - should be self explanatory 
    for pair in club_information:
        id_to_name[int(pair[0])] = pair[1]

    return id_to_name
    # remember to clean up with closing connection at end; share connection with db
    # insert to prevent continually opening connection (improves speed)
