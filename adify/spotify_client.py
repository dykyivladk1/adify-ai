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


