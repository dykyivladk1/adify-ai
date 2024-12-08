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


def test_retries_on_429(monkeypatch):
    monkeypatch.setattr("adify.spotify_client.time.sleep", lambda s: None)
    client = SpotifyClient(lambda: "token")
    client._http.request = MagicMock(side_effect=[_resp(429, headers={"Retry-After": "1"}), _resp(body={"id": "me"})])
    assert client.me() == {"id": "me"}


def test_raises_with_spotify_message():
    client = SpotifyClient(lambda: "token", max_retries=0)
    client._http.request = MagicMock(return_value=_resp(403, {"error": {"message": "nope"}}))
    with pytest.raises(SpotifyError, match="nope"):
        client.me()


def test_add_to_playlist_chunks_by_100():
    client = SpotifyClient(lambda: "token")
    client._http.request = MagicMock(return_value=_resp(body={"snapshot_id": "x"}))
    client.add_to_playlist("pl", [f"spotify:track:{i}" for i in range(250)])
    sizes = [len(c.kwargs["json"]["uris"]) for c in client._http.request.call_args_list]
    assert sizes == [100, 100, 50]
    assert client._http.request.call_args.args[1].endswith("playlists/pl/items")
