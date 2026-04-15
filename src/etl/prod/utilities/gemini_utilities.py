
import typing
from typing import Any, Dict, List
from collections import defaultdict


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