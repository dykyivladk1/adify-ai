from unittest.mock import MagicMock

import pytest

from adify.spotify_client import SpotifyClient, SpotifyError


def _resp(status=200, body=None, headers=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = body or {}
    r.content = b"x"
    r.headers = headers or {}
    return r


