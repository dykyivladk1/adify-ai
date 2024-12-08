from adify.harvester import Harvester, track_from_api
from adify.prompt_parser import SearchTask


def _api_track(i, artist_id="a1"):
    return {
        "id": f"t{i}",
        "name": f"Song {i}",
        "artists": [{"id": artist_id, "name": artist_id.upper()}],
        "album": {"name": "Album", "release_date": "1994-05-01"},
        "explicit": False,
    }


class FakeSpotify:
    def __init__(self):
        self.artist_calls = 0

    def search(self, query, kind, limit=30):
        if kind == "artist":
            return iter([{"id": "a9", "name": "A9", "genres": ["ambient"]}])
        return iter([_api_track(1), _api_track(2), _api_track(1)])  # duplicate on purpose

    def artist(self, artist_id):
        self.artist_calls += 1
        return {"genres": ["trip hop"]}

    def artist_albums(self, artist_id, limit=5):
        return [{"id": "al1", "name": "Deep", "release_date": "2001"}]

    def album_tracks(self, album_id, limit=20):
        return [{"id": "t50", "name": "Deep Track", "artists": [{"id": "a9", "name": "A9"}]}]


