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


def _year(release_date: str | None) -> int | None:
    if release_date and release_date[:4].isdigit():
        return int(release_date[:4])
    return None


def track_from_api(item: dict, album: dict | None = None, tags: list[str] | None = None) -> Track | None:
    album = album or item.get("album") or {}
    if not item.get("id") or item.get("is_local"):
        return None
    return Track(
        id=item["id"],
        name=item.get("name", ""),
        artists=[a["name"] for a in item.get("artists", [])],
        artist_ids=[a["id"] for a in item.get("artists", []) if a.get("id")],
        album=album.get("name", ""),
        release_year=_year(album.get("release_date")),
        tags=list(tags or []),
        explicit=bool(item.get("explicit")),
    )


