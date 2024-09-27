"""Pulls tracks from Spotify for a prompt and pushes them into Qdrant.

This is what replaces the static dataset: every prompt that the catalog can't
answer well yet triggers a small, bounded crawl, and the results stay in
Qdrant for the next person asking for something similar.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from .models import Track
from .prompt_parser import SearchTask
from .spotify_client import SpotifyClient, SpotifyError
from .vector_store import TrackStore

log = logging.getLogger(__name__)

ARTISTS_TO_EXPAND = 4
ALBUMS_PER_ARTIST = 2
TRACKS_PER_ALBUM = 8
MAX_GENRE_LOOKUPS = 20


