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


def test_track_from_api_parses_year():
    track = track_from_api(_api_track(1), tags=["x"])
    assert track.release_year == 1994 and track.tags == ["x"]
    assert track_from_api({"id": None}) is None


def test_harvest_dedupes_and_attaches_genres(store):
    spotify = FakeSpotify()
    harvester = Harvester(spotify, store)
    stored = harvester.run([
        SearchTask("track", 'genre:"trip hop"', tags=["trip hop"]),
        SearchTask("artist", 'genre:"ambient"', tags=["ambient"]),
    ])

    assert stored == 3
    assert store.count() == 3
    # a1 genres come from one lookup, a9's from the artist search result (no lookup)
    assert spotify.artist_calls == 1
    hits = {h.track.id: h.track for h in store.search(store.embedder.encode(["deep"])[0], limit=10)}
    assert hits["t50"].genres == ["ambient"]
    assert hits["t50"].album == "Deep"
    assert hits["t1"].genres == ["trip hop"]
