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


def test_search_pages_ten_at_a_time():
    client = SpotifyClient(lambda: "token")
    pages = [
        _resp(body={"tracks": {"items": [{"id": str(i)} for i in range(10)], "next": "more"}}),
        _resp(body={"tracks": {"items": [{"id": "last"}], "next": None}}),
    ]
    client._http.request = MagicMock(side_effect=pages)

    items = list(client.search("rock", "track", limit=30))

    assert len(items) == 11
    offsets = [call.kwargs["params"]["offset"] for call in client._http.request.call_args_list]
    assert offsets == [0, 10]


