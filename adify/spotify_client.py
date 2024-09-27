"""Thin Spotify Web API wrapper.

We only use spotipy for the OAuth / client-credentials dance. The actual calls go
through requests because spotipy still targets a few endpoints that Spotify
removed in the Feb 2026 dev-mode update (POST /users/{id}/playlists,
/playlists/{id}/tracks) and search is now capped at 10 results per page.
"""
from __future__ import annotations

import logging
import time
from typing import Callable, Iterator

import requests

log = logging.getLogger(__name__)

API_BASE = "https://api.spotify.com/v1"
SEARCH_PAGE_SIZE = 10  # hard max since Feb 2026


class SpotifyError(RuntimeError):
    def __init__(self, status: int, message: str):
        super().__init__(f"Spotify API {status}: {message}")
        self.status = status


class SpotifyClient:
    def __init__(self, token_provider: Callable[[], str], timeout: float = 10.0, max_retries: int = 3):
        # token_provider is called before every request so spotipy's auth managers
        # can transparently refresh expired tokens.
        self._token_provider = token_provider
        self._timeout = timeout
        self._max_retries = max_retries
        self._http = requests.Session()

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = path if path.startswith("http") else f"{API_BASE}/{path.lstrip('/')}"

        for attempt in range(self._max_retries + 1):
            headers = {"Authorization": f"Bearer {self._token_provider()}"}
            resp = self._http.request(method, url, headers=headers, timeout=self._timeout, **kwargs)

            if resp.status_code == 429 and attempt < self._max_retries:
                wait = int(resp.headers.get("Retry-After", "1"))
                log.warning("Rate limited by Spotify, sleeping %ss", wait)
                time.sleep(min(wait, 30))
                continue
            if resp.status_code >= 500 and attempt < self._max_retries:
                time.sleep(2 ** attempt)
                continue
            break

        if resp.status_code >= 400:
            try:
                message = resp.json().get("error", {}).get("message", resp.text)
            except ValueError:
                message = resp.text
            raise SpotifyError(resp.status_code, message)

        return resp.json() if resp.content else {}

    # --- catalog -----------------------------------------------------------

    def search(self, query: str, kind: str, limit: int = 30) -> Iterator[dict]:
        """Yield up to `limit` items for a search, paging 10 at a time."""
        key = f"{kind}s"
        offset = 0
        while offset < limit:
            page = self._request(
                "GET",
                "search",
                params={"q": query, "type": kind, "limit": SEARCH_PAGE_SIZE, "offset": offset},
            )
            items = [i for i in page.get(key, {}).get("items", []) if i]
            yield from items
            if len(items) < SEARCH_PAGE_SIZE or not page[key].get("next"):
                return
            offset += SEARCH_PAGE_SIZE

    def artist(self, artist_id: str) -> dict:
        return self._request("GET", f"artists/{artist_id}")

    def artist_albums(self, artist_id: str, limit: int = 5) -> list[dict]:
        page = self._request(
            "GET",
            f"artists/{artist_id}/albums",
            params={"include_groups": "album,single", "limit": limit},
        )
        return page.get("items", [])

    def album_tracks(self, album_id: str, limit: int = 20) -> list[dict]:
        page = self._request("GET", f"albums/{album_id}/tracks", params={"limit": limit})
        return page.get("items", [])

    # --- user --------------------------------------------------------------

    def me(self) -> dict:
        return self._request("GET", "me")

    def create_playlist(self, name: str, description: str = "", public: bool = True) -> dict:
        return self._request(
            "POST",
            "me/playlists",
            json={"name": name, "description": description[:300], "public": public},
        )

    def add_to_playlist(self, playlist_id: str, uris: list[str]) -> None:
        for start in range(0, len(uris), 100):
            self._request("POST", f"playlists/{playlist_id}/items", json={"uris": uris[start:start + 100]})
