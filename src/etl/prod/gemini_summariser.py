"""
etl/prod/gemini_summariser.py

Production Gemini summariser for scraped Instagram posts.
based on original testing file but with additions in the form of
best practice (and new data types + paths tie in)

Design goals
------------
1) Keep the input/output contract simple:
   - Input: a list of post dicts (from the scraper batch_list)
   - Output: a list of summary records (one per club_id)

2) Be safe for production:
   - Batch the request so we don't underutilise context windows.
   - Never lose raw data (raw JSONL is written by the scraper already).
   - Persist derived summaries to disk under `insta_news_data_root/derived/...`.
   - Best-effort persist to DB (`ai_summaries`) for website reads.

3) Be easy to iterate on:
   - All prompt/model config lives in one place.
   - The file name format makes it easy to re-run and compare versions.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List
from zoneinfo import ZoneInfo

from src.etl.prod import data_paths
from src.etl.prod.post_time_window import infer_summary_time_window
from src.etl.prod.prompts.system_prompts import SYSTEM_PROMPTS

from google import genai
from google.genai import types

# for the db insertion
import sqlite3

from src.etl.prod.db_insertion_tools.db_insert import db_insert_gemini_summaries
from src.etl.prod.utilities import gemini_utilities

DB_PATH = os.getenv("insta_news_db_path")

# -----------------------------------------------------------------------------
# 1) Configuration
# -----------------------------------------------------------------------------
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
MODEL_LIST = [
    DEFAULT_MODEL,                # typically "gemini-2.5-flash-lite" or overridable by env
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite-preview", 
]
DEFAULT_PROMPT_NAME = os.getenv("GEMINI_SYSTEM_PROMPT", "concise_cot")


def _get_system_prompt(name: str) -> str:
    """
    Resolve a system prompt by name from `prompts/system_prompts.py`.

    Teaching note:
    - This lets you quickly try different prompt variants without touching the summariser logic.
    - If you typo the name, we fall back to "concise_cot" instead of crashing mid-run.
    """
    prompt_template = (SYSTEM_PROMPTS.get(name) or SYSTEM_PROMPTS["concise_cot"]).strip()
    # If the template includes a placeholder, inject a fresh "now" string at call time.
    # This is how your `concise_cot` prompt gets the correct CURRENT_TIME value.
    if "{current_time_str}" in prompt_template:
        melb_tz = ZoneInfo("Australia/Melbourne")
        current_time_str = datetime.now(melb_tz).strftime("%A, %B %d, %Y at %I:%M %p")
        prompt_template = prompt_template.replace("{current_time_str}", current_time_str)
        return prompt_template
    raise ValueError(f"SYSTEM PROMPT NAME: {name} is not valid")


def _get_client():
    """
    Create a Gemini client using `genai_api_key` from the environment.

    Teaching note:
    - We keep secrets out of code and rely on `.env` + environment variables.
    - If this key is missing, we fail fast with a clear error.
    """
    api_key = os.getenv("genai_api_key")
    if not api_key:
        raise RuntimeError("Missing env var `genai_api_key` (Gemini API key).")
    return genai.Client(api_key=api_key)


# should switch to updating class and struct fields instead of having like 
# 5 different parameters to pass in
# @dataclass(frozen=True)
# class SummaryRecord:
#     club_id: int
#     run_date: str
#     window: Dict[str, str]
#     payload: Dict[str, Any]
#     output_path: Path


# note move to its own module
def backup_to_disk(club_id: int, payload: json) -> None:
    '''
    Takes the produced ai output and writes it to disk for cold memory storage
    '''
    # load class that stores all path information
    paths = data_paths.get_paths()
    # so that the data is navigatable
    run_date = datetime.now().date().isoformat()

    # receive the location to store the data
    out_dir = data_paths.ensure_dir(paths.summary_dir(club_id=club_id, date_yyyy_mm_dd=run_date))
    out_path = out_dir / f"summary_{run_date}.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def call_ai_model(club_id: int, club_posts: Dict[int, Any], id_to_name: Dict[int, str]) -> json:
    '''
    use the api to call the model to generate the summary 

    currently using: Gemini
    '''
    # set up the necessary variables (can pass in for all gens but the signuture becomes ugly)
    client = _get_client()
    system_prompt = _get_system_prompt(DEFAULT_PROMPT_NAME)
    selected_ai_model = DEFAULT_MODEL

    
    # send field model can use to build the response.
    model_input = {
        "club_name": id_to_name.get(club_id),
        "club_id": club_id,
        "posts": [
            {
                "post_id": p.get("post_id"),
                "timestamp": p.get("time_metadata_utc") or p.get("date_local"),
                "caption": p.get("caption") or "",
                "link": p.get("link"),
            }
            for p in club_posts
        ],
    }

    # TODO: implement model cycling - should be robust - otherwise implement 
    #       exponential back off for retrying haulting program execution 
    # try: 
    #  for candidate_model in MODEL_LIST:
    #               ... code ...
    #    except Exception as e:
    #     print(f"[WARN] model {model} failed: {e}")
    #     continue 
    print(f"Generating summary for {club_id} using model: {selected_ai_model}")
    response = client.models.generate_content(
        model=selected_ai_model, 
        contents=json.dumps(model_input, ensure_ascii=False),
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            # forcing JSON output makes downstream parsing reliable
            response_mime_type="application/json",
        ),
    )


    return response



def gemini_summariser(
    all_posts: List[Dict[str, Any]],
    *, # following fields need to be specified by name
    batch_size: int = 50,
) -> None:
    """
    Summarise a mixed batch of post dicts coming from the scraper.

    Expected post dict shape (minimum):
      {
        "club_id": int,
        "post_id": str,
        "caption": str,
        "date_local": str,
        "time_metadata_utc": str,
        "link": str
      }

    Behavior:
    - Groups posts by club_id (you want one summary per club, not a cross-club soup).
    - For each club_id group the posts
    - Writes each summary JSON to:
        derived/summaries/club_id=<ID>/date=<RUN_DATE>/summary_<N>.json
        and inserts into db
    - Also upserts condensed summary into DB table `ai_summaries`.
    """
    if not all_posts:
        return []

    
    # split the posts by club
    club_posts = gemini_utilities.group_by_club(all_posts)
 
    # Single connection to speed up execution
    conn = sqlite3.Connection(DB_PATH)
    
    # create lookup table to insert the club name into each ai query
    id_to_name = gemini_utilities.create_club_lookup_table(conn)

    # do for each club scraped for
    for club_id, club_posts in club_posts.items():        
        
        # Keep newest->oldest stable ordering if your scraper appended in that order.
        # If ordering matters later, you can sort by time_metadata_utc here.
        window = infer_summary_time_window(club_posts)
        
        # call the ai api and produce response
        response = call_ai_model(club_id, club_posts, id_to_name)

        if not response:
            print("[WARN] no response from any models")
            return 

        # Response should already be JSON, if not throw an error.
        try:
            payload = json.loads(response.text or "{}")
        except json.JSONDecodeError:
            print("Error with the ai produced json response")
            return 

        # link metadata to outputted json information
        payload.setdefault("club_id", club_id)
        payload.setdefault("window", window)
        payload.setdefault(
            "source_posts",
            [{"post_id": p.get("post_id"), "link": p.get("link")} for p in club_posts],
        )
        
        # disk backup in json should the db be compromised
        backup_to_disk(club_id, payload)

        # insert the information into the db
        db_insert_gemini_summaries(payload, conn)
        



