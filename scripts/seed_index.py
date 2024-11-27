"""Warm up the Qdrant catalog so the first users don't wait on Spotify.

    python -m scripts.seed_index                 # default moods/genres
    python -m scripts.seed_index "jazz" "90s rap"  # your own prompts

Uses client credentials, no user login needed.
"""
import logging
import sys
import time

from adify.config import settings
from adify.prompt_parser import build_search_plan, parse_prompt
from adify.services import get_harvester, get_store

DEFAULT_PROMPTS = [
    "chill lo-fi for studying",
    "indie rock road trip",
    "90s hip hop",
    "sad acoustic songs",
    "house music party",
    "synthwave night drive",
    "jazz for dinner",
    "workout phonk and trap",
    "ambient music for sleep",
    "happy summer pop",
    "classic soul and funk",
    "heavy metal",
    "r&b love songs",
    "reggaeton summer",
    "techno",
    "folk morning coffee",
]


