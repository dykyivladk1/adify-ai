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


class Harvester:
    def __init__(self, spotify: SpotifyClient, store: TrackStore):
        self.spotify = spotify
        self.store = store
        # artist genres barely change, cache them for the process lifetime
        self._artist_genres = lru_cache(maxsize=5000)(self._fetch_artist_genres)

    def _fetch_artist_genres(self, artist_id: str) -> tuple[str, ...]:
        try:
            return tuple(self.spotify.artist(artist_id).get("genres", []))
        except SpotifyError as exc:
            log.debug("genre lookup failed for %s: %s", artist_id, exc)
            return ()

    def run(self, tasks: list[SearchTask]) -> int:
        tracks: dict[str, Track] = {}
        known_genres: dict[str, list[str]] = {}

        for task in tasks:
            try:
                if task.kind == "artist":
                    self._harvest_artists(task, tracks, known_genres)
                else:
                    self._harvest_tracks(task, tracks)
            except SpotifyError as exc:
                # one broken query shouldn't kill the whole request
                log.warning("search %r failed: %s", task.query, exc)

        self._attach_genres(tracks.values(), known_genres)
        stored = self.store.upsert(list(tracks.values()))
        log.info("harvested %d tracks from %d searches", stored, len(tasks))
        return stored

    def _add(self, tracks: dict[str, Track], track: Track | None) -> None:
        if track is None:
            return
        if track.id in tracks:
            existing = tracks[track.id]
            existing.tags = list(dict.fromkeys(existing.tags + track.tags))
        else:
            tracks[track.id] = track

    def _harvest_tracks(self, task: SearchTask, tracks: dict[str, Track]) -> None:
        for item in self.spotify.search(task.query, "track", limit=task.limit):
            self._add(tracks, track_from_api(item, tags=task.tags))

    def _harvest_artists(self, task: SearchTask, tracks: dict[str, Track], known_genres: dict) -> None:
        # Top-tracks endpoint is gone, so go artist -> latest albums -> album tracks.
        artists = list(self.spotify.search(task.query, "artist", limit=task.limit))
        for artist in artists:
            known_genres[artist["id"]] = artist.get("genres", [])

        for artist in artists[:ARTISTS_TO_EXPAND]:
            for album in self.spotify.artist_albums(artist["id"], limit=ALBUMS_PER_ARTIST):
                for item in self.spotify.album_tracks(album["id"], limit=TRACKS_PER_ALBUM):
                    self._add(tracks, track_from_api(item, album=album, tags=task.tags))

    def _attach_genres(self, tracks, known_genres: dict[str, list[str]]) -> None:
        lookups = 0
        for track in tracks:
            artist_id = track.main_artist_id
            if not artist_id:
                continue
            if artist_id not in known_genres:
                if lookups >= MAX_GENRE_LOOKUPS:
                    continue
                known_genres[artist_id] = list(self._artist_genres(artist_id))
                lookups += 1
            track.genres = known_genres[artist_id]
